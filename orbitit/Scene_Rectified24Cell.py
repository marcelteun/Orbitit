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
#-------------------------------------------------------------------

import wx
import logging
import math
from OpenGL.GL import glBlendFunc, glEnable, GL_SRC_ALPHA, GL_BLEND, GL_ONE_MINUS_SRC_ALPHA

from orbitit import Geom3D, Geom4D, rgb

TITLE = 'Rectified 24-Cell'

#V2 = 1.0
V2  = math.sqrt(2)
dV2 = 2*V2

Vs = [
        [  0,  V2,  V2,  dV2],  #  0
        [ V2,   0,  V2,  dV2],  #  1
        [  0, -V2,  V2,  dV2],  #  2
        [-V2,   0,  V2,  dV2],  #  3
        [ V2,  V2,   0,  dV2],  #  4
        [ V2, -V2,   0,  dV2],  #  5
        [-V2, -V2,   0,  dV2],  #  6
        [-V2,  V2,   0,  dV2],  #  7
        [  0,  V2, -V2,  dV2],  #  8
        [ V2,   0, -V2,  dV2],  #  9
        [  0, -V2, -V2,  dV2],  # 10
        [-V2,   0, -V2,  dV2],  # 11

        [  0,  V2,  V2, -dV2],  # 12
        [ V2,   0,  V2, -dV2],  # 13
        [  0, -V2,  V2, -dV2],  # 14
        [-V2,   0,  V2, -dV2],  # 15
        [ V2,  V2,   0, -dV2],  # 16
        [ V2, -V2,   0, -dV2],  # 17
        [-V2, -V2,   0, -dV2],  # 18
        [-V2,  V2,   0, -dV2],  # 19
        [  0,  V2, -V2, -dV2],  # 20
        [ V2,   0, -V2, -dV2],  # 21
        [  0, -V2, -V2, -dV2],  # 22
        [-V2,   0, -V2, -dV2],  # 23

        [  0,  V2,  dV2,  V2],  # 24
        [ V2,   0,  dV2,  V2],  # 25
        [  0, -V2,  dV2,  V2],  # 26
        [-V2,   0,  dV2,  V2],  # 27
        [ V2,  V2,  dV2,   0],  # 28
        [ V2, -V2,  dV2,   0],  # 29
        [-V2, -V2,  dV2,   0],  # 30
        [-V2,  V2,  dV2,   0],  # 31
        [  0,  V2,  dV2, -V2],  # 32
        [ V2,   0,  dV2, -V2],  # 33
        [  0, -V2,  dV2, -V2],  # 34
        [-V2,   0,  dV2, -V2],  # 35

        [  0,  V2, -dV2,  V2],  # 36
        [ V2,   0, -dV2,  V2],  # 37
        [  0, -V2, -dV2,  V2],  # 38
        [-V2,   0, -dV2,  V2],  # 39
        [ V2,  V2, -dV2,   0],  # 40
        [ V2, -V2, -dV2,   0],  # 41
        [-V2, -V2, -dV2,   0],  # 42
        [-V2,  V2, -dV2,   0],  # 43
        [  0,  V2, -dV2, -V2],  # 44
        [ V2,   0, -dV2, -V2],  # 45
        [  0, -V2, -dV2, -V2],  # 46
        [-V2,   0, -dV2, -V2],  # 47

        [  0,  dV2,  V2,  V2],  # 48
        [ V2,  dV2,   0,  V2],  # 49
        [  0,  dV2, -V2,  V2],  # 50
        [-V2,  dV2,   0,  V2],  # 51
        [ V2,  dV2,  V2,   0],  # 52
        [ V2,  dV2, -V2,   0],  # 53
        [-V2,  dV2, -V2,   0],  # 54
        [-V2,  dV2,  V2,   0],  # 55
        [  0,  dV2,  V2, -V2],  # 56
        [ V2,  dV2,   0, -V2],  # 57
        [  0,  dV2, -V2, -V2],  # 58
        [-V2,  dV2,   0, -V2],  # 59

        [  0, -dV2,  V2,  V2],  # 60
        [ V2, -dV2,   0,  V2],  # 61
        [  0, -dV2, -V2,  V2],  # 62
        [-V2, -dV2,   0,  V2],  # 63
        [ V2, -dV2,  V2,   0],  # 64
        [ V2, -dV2, -V2,   0],  # 65
        [-V2, -dV2, -V2,   0],  # 66
        [-V2, -dV2,  V2,   0],  # 67
        [  0, -dV2,  V2, -V2],  # 68
        [ V2, -dV2,   0, -V2],  # 69
        [  0, -dV2, -V2, -V2],  # 70
        [-V2, -dV2,   0, -V2],  # 71

        [dV2,   0,   V2,  V2],  # 72
        [dV2,  V2,    0,  V2],  # 73
        [dV2,   0,  -V2,  V2],  # 74
        [dV2, -V2,    0,  V2],  # 75
        [dV2,  V2,   V2,   0],  # 76
        [dV2,  V2,  -V2,   0],  # 77
        [dV2, -V2,  -V2,   0],  # 78
        [dV2, -V2,   V2,   0],  # 79
        [dV2,   0,   V2, -V2],  # 80
        [dV2,  V2,    0, -V2],  # 81
        [dV2,   0,  -V2, -V2],  # 82
        [dV2, -V2,    0, -V2],  # 83

        [-dV2,   0,  V2,  V2],  # 84
        [-dV2,  V2,   0,  V2],  # 85
        [-dV2,   0, -V2,  V2],  # 86
        [-dV2, -V2,   0,  V2],  # 87
        [-dV2,  V2,  V2,   0],  # 88
        [-dV2,  V2, -V2,   0],  # 89
        [-dV2, -V2, -V2,   0],  # 90
        [-dV2, -V2,  V2,   0],  # 91
        [-dV2,   0,  V2, -V2],  # 92
        [-dV2,  V2,   0, -V2],  # 93
        [-dV2,   0, -V2, -V2],  # 94
        [-dV2, -V2,   0, -V2],  # 95
    ]

# 24 cubes
Cubes0_Cs = [
    # shell 3 (6 cubes): inner shell of cubes just outside centre cell:
    [ # 0.0
        [0+12, 8+24, 9+24, 1+12], [9+24, 1+12, 2+12, 10+24],
        [2+12, 10+24, 11+24, 3+12], [11+24, 3+12, 0+12, 8+24],
        [0+12, 1+12, 2+12, 3+12], [8+24, 9+24, 10+24, 11+24],                   # + Z
    ],
    [ # 0.1
        [8+12, 8+36, 9+36, 9+12], [9+36, 9+12, 10+12, 10+36],
        [10+12, 10+36, 11+36, 11+12], [11+36, 11+12, 8+12, 8+36],
        [8+12, 9+12, 10+12, 11+12], [8+36, 9+36, 10+36, 11+36],                 # - Z
    ],
    # shell 2 (12 cubes):
    [ # 0.2
        [1+48, 1+72, 5+72, 5+48], [5+72, 5+48, 9+48, 9+72],
        [9+48, 9+72, 4+72, 4+48], [4+72, 4+48, 1+48, 1+72],
        [1+48, 5+48, 9+48, 4+48], [1+72, 5+72, 9+72, 4+72],                     # centre layer NE
    ],
    [ # 0.3
        [3+60, 3+84, 6+84, 6+60], [6+84, 6+60, 11+60, 11+84],
        [11+60, 11+84, 7+84, 7+60], [7+84, 7+60, 3+60, 3+84],
        [3+60, 6+60, 11+60, 7+60], [3+84, 6+84, 11+84, 7+84],                   # centre layer SW
    ],
    [ # 0.4
        [3+72, 1+60, 5+60, 6+72], [5+60, 6+72, 11+72, 9+60],
        [11+72, 9+60, 4+60, 7+72], [4+60, 7+72, 3+72, 1+60],
        [3+72, 6+72, 11+72, 7+72], [1+60, 5+60, 9+60, 4+60],                    # centre layer SE
    ],
    [ # 0.5
        [1+84, 3+48, 6+48, 5+84], [6+48, 5+84, 9+84, 11+48],
        [9+84, 11+48, 7+48, 4+84], [7+48, 4+84, 1+84, 3+48],
        [1+84, 5+84, 9+84, 4+84], [3+48, 6+48, 11+48, 7+48],                    # centre layer NW
    ],
    # shell 1 (6 cubes): shell of cubes just inside outer shell:
    [ # 0.6
        [0, 1, 2, 3], [0+24, 1+24, 2+24, 3+24],
        [0, 1, 25, 24], [1, 2, 26, 25], [2, 3, 27, 26], [3, 0, 24, 27],         # + Z
    ],
    [ # 0.7
        [8, 9, 10, 11], [0+36, 1+36, 2+36, 3+36],
        [8, 9, 37, 36], [9, 10, 38, 37], [10, 11, 39, 38], [11, 8, 36, 39],     # - Z
    ],
]
Cubes0_Cols = [
    [0, 0, 0, 0, 0, 0] for cell in Cubes0_Cs
]

Cubes1_Cs = [
    # shell 3 (6 cubes): inner shell of cubes just outside centre cell:
    [ # 1.0
        [1+12, 8+72, 11+72, 5+12], [11+72, 5+12, 9+12, 10+72],
        [9+12, 10+72, 9+72, 4+12], [9+72, 4+12, 1+12, 8+72],
        [1+12, 5+12, 9+12, 4+12], [8+72, 11+72, 10+72, 9+72],                   # + X
    ],
    [ # 1.1
        [3+12, 8+84, 11+84, 6+12], [11+84, 6+12, 11+12, 10+84],
        [11+12, 10+84, 9+84, 7+12], [9+84, 7+12, 3+12, 8+84],
        [3+12, 6+12, 11+12, 7+12], [8+84, 11+84, 10+84, 9+84],                  # - X
    ],
    # shell 2 (12 cubes):
    [ # 1.2
        [26, 60, 64, 29], [64, 29, 34, 68], [34, 68, 67, 30], [67, 30, 26, 60],
        [2+24, 6+24, 10+24, 5+24], [0+60, 4+60, 8+60, 7+60],                    # front layer South
    ],
    [ # 1.3
        [2+48, 0+36, 4+36, 5+48], [4+36, 5+48, 10+48, 8+36],
        [10+48, 8+36, 7+36, 6+48], [7+36, 6+48, 2+48, 0+36],
        [2+48, 5+48, 10+48, 6+48], [0+36, 4+36, 8+36, 7+36],                    # back layer North
    ],
    [ # 1.4
        [24, 48, 52, 28], [52, 28, 32, 56], [32, 56, 55, 31], [55, 31, 24, 48],
        [0+24, 4+24, 8+24, 7+24], [0+48, 4+48, 8+48, 7+48],                     # front layer North
    ],
    [ # 1.5
        [2+60, 2+36, 6+36, 6+60], [6+36, 6+60, 10+60, 10+36],
        [10+60, 10+36, 5+36, 5+60], [5+36, 5+60, 2+60, 2+36],
        [2+60, 6+60, 10+60, 5+60], [2+36, 6+36, 10+36, 5+36],                   # back layer South
    ],
    # shell 1 (6 cubes): shell of cubes just inside outer shell:
    [ # 1.6
        [1, 5, 9, 4], [0+72, 1+72, 2+72, 3+72],
        [1, 5, 75, 72], [5, 9, 74, 75], [9, 4, 73, 74], [4, 1, 72, 73],         # + X
    ],
    [ # 1.7
        [3, 7, 11, 6], [0+84, 1+84, 2+84, 3+84],
        [6, 3, 84, 87], [3, 7, 85, 84], [7, 11, 86, 85], [11, 6, 87, 86],       # - X
    ],
]
Cubes1_Cols = [
    [1, 1, 1, 1, 1, 1] for cell in Cubes1_Cs
]

Cubes2_Cs = [
    # shell 3 (6 cubes): inner shell of cubes just outside centre cell:
    [ # 2.0
        [0+12, 8+48, 9+48, 4+12], [9+48, 4+12, 8+12, 10+48],
        [8+12, 10+48, 11+48, 7+12], [11+48, 7+12, 0+12, 8+48],
        [0+12, 4+12, 8+12, 7+12], [8+48, 9+48, 10+48, 11+48],                   # + Y
    ],
    [ # 2.1
        [2+12, 8+60, 9+60, 5+12], [9+60, 5+12, 10+12, 10+60],
        [10+12, 10+60, 11+60, 6+12], [11+60, 6+12, 2+12, 8+60],
        [2+12, 5+12, 10+12, 6+12], [8+60, 9+60, 10+60, 11+60],                  # - Y
    ],
    # shell 2 (12 cubes):
    [ # 2.2
        [25, 72, 76, 28], [76, 28, 33, 80], [33, 80, 79, 29], [79, 29, 25, 72],
        [1+24, 5+24, 9+24, 4+24], [0+72, 4+72, 8+72, 7+72],                     # front layer East
    ],
    [ # 2.3
        [2+84, 3+36, 7+36, 5+84], [7+36, 5+84, 10+84, 11+36],
        [10+84, 11+36, 6+36, 6+84], [6+36, 6+84, 2+84, 3+36],
        [2+84, 5+84, 10+84, 6+84], [3+36, 7+36, 11+36, 6+36],                   # back layer West
    ],
    [ # 2.4
        [3+24, 0+84, 4+84, 7+24], [4+84, 7+24, 11+24, 8+84],
        [11+24, 8+84, 7+84, 6+24], [7+84, 6+24, 3+24, 0+84],
        [3+24, 7+24, 11+24, 6+24], [0+84, 4+84, 8+84, 7+84],                    # front layer West
    ],
    [ # 2.5
        [2+72, 1+36, 5+36, 6+72], [5+36, 6+72, 10+72, 9+36],
        [10+72, 9+36, 4+36, 5+72], [4+36, 5+72, 2+72, 1+36],
        [2+72, 6+72, 10+72, 5+72], [1+36, 5+36, 9+36, 4+36],                    # back layer East
    ],
    # shell 1 (6 cubes): shell of cubes just inside outer shell:
    [ # 2.6
        [0, 4, 8, 7], [0+48, 1+48, 2+48, 3+48],
        [0, 4, 49, 48], [4, 8, 50, 49], [8, 7, 51, 50], [7, 0, 48, 51],         # + Y
    ],
    [ # 2.7
        [2, 6, 10, 5], [0+60, 1+60, 2+60, 3+60],
        [2, 6, 63, 60], [6, 10, 62, 63], [10, 5, 61, 62], [5, 2, 60, 61],       # - Y
    ],
]
Cubes2_Cols = [
    [2, 2, 2, 2, 2, 2] for cell in Cubes2_Cs
]

Cubos0_Cs = [
    # inner cell
    [
        [13, 14, 17], [14, 15, 18], [15, 12, 19], [12, 13, 16],
        [17, 22, 21], [18, 23, 22], [19, 20, 23], [16, 21, 20],
        [0+12, 1+12, 2+12, 3+12], [8+12, 9+12, 10+12, 11+12],
        [1+12, 5+12, 9+12, 4+12], [3+12, 6+12, 11+12, 7+12],
        [0+12, 4+12, 8+12, 7+12], [2+12, 5+12, 10+12, 6+12]
    ],
    # front cell
    [
        [24, 25, 28], [25, 26, 29], [26, 27, 30], [27, 24, 31],
        [28, 33, 32], [29, 34, 33], [30, 35, 34], [31, 32, 35],
        [8+24, 9+24, 10+24, 11+24], [0+24, 1+24, 2+24, 3+24],
        [2+24, 6+24, 10+24, 5+24], [0+24, 4+24, 8+24, 7+24],
        [1+24, 5+24, 9+24, 4+24], [3+24, 7+24, 11+24, 6+24]
    ],
    # back cell
    [
        [39, 36, 43], [36, 37, 40], [37, 38, 41], [38, 39, 42],
        [43, 44, 47], [40, 45, 44], [41, 46, 45], [42, 47, 46],
        [8+36, 9+36, 10+36, 11+36], [0+36, 1+36, 2+36, 3+36],
        [2+36, 6+36, 10+36, 5+36], [0+36, 4+36, 8+36, 7+36],
        [3+36, 7+36, 11+36, 6+36], [1+36, 5+36, 9+36, 4+36]
    ],
    # top cell
    [
        [48, 49, 52], [49, 50, 53], [50, 51, 54], [51, 48, 55],
        [52, 57, 56], [53, 58, 57], [54, 59, 58], [55, 56, 59],
        [1+48, 5+48, 9+48, 4+48], [3+48, 6+48, 11+48, 7+48],
        [2+48, 5+48, 10+48, 6+48], [0+48, 4+48, 8+48, 7+48],
        [8+48, 9+48, 10+48, 11+48], [0+48, 1+48, 2+48, 3+48]
    ],
    # bottom cell
    [
        [63, 60, 67], [60, 61, 64], [61, 62, 65], [62, 63, 66],
        [67, 68, 71], [64, 69, 68], [65, 70, 69], [66, 71, 70],
        [3+60, 6+60, 11+60, 7+60], [1+60, 5+60, 9+60, 4+60],
        [2+60, 6+60, 10+60, 5+60], [0+60, 4+60, 8+60, 7+60],
        [8+60, 9+60, 10+60, 11+60], [0+60, 1+60, 2+60, 3+60]
    ],
    # right cell
    [
        [72, 73, 76], [73, 74, 77], [74, 75, 78], [75, 72, 79],
        [76, 81, 80], [77, 82, 81], [78, 83, 82], [79, 80, 83],
        [1+72, 5+72, 9+72, 4+72], [3+72, 6+72, 11+72, 7+72],
        [8+72, 11+72, 10+72, 9+72], [0+72, 1+72, 2+72, 3+72],
        [0+72, 4+72, 8+72, 7+72], [2+72, 6+72, 10+72, 5+72]
    ],
    # left cell
    [
        [87, 84, 91], [84, 85, 88], [85, 86, 89], [86, 87, 90],
        [91, 92, 95], [88, 93, 92], [89, 94, 93], [90, 95, 94],
        [3+84, 6+84, 11+84, 7+84], [1+84, 5+84, 9+84, 4+84],
        [8+84, 11+84, 10+84, 9+84], [0+84, 1+84, 2+84, 3+84],
        [2+84, 5+84, 10+84, 6+84], [0+84, 4+84, 8+84, 7+84]
    ],
    # outer cell
    [
        [0, 1, 4], [1, 2, 5], [2, 3, 6], [3, 0, 7],
        [4, 9, 8], [5, 10, 9], [6, 11, 10], [7, 8, 11],
        [0, 1, 2, 3], [8, 9, 10, 11],
        [3, 7, 11, 6], [6, 3, 84, 87],
        [0, 4, 8, 7], [2, 6, 10, 5],
    ]
]
Cubos0_Cols = [
    [3, 4, 3, 4, 4, 3, 4, 3, 0, 0, 1, 1, 2, 2] for cell in Cubos0_Cs
]

Cubos1_Cs = [
    [
        # front bottom right (inner)
        [14, 34, 68], [17, 83, 69], [29, 64, 79], [13, 33, 80],
        [13, 14, 17], [29, 34, 33], [64, 69, 68], [79, 80, 83],
        [9+24, 1+12, 2+12, 10+24], [11+72, 9+60, 4+60, 7+72],
        [1+12, 8+72, 11+72, 5+12], [64, 29, 34, 68],
        [2+12, 8+60, 9+60, 5+12], [33, 80, 79, 29]
    ],
    [
        # front top left (inner)
        [19, 59, 93], [15, 35, 92], [12, 32, 56], [31, 55, 88],
        [15, 12, 19], [31, 32, 35], [55, 56, 59], [88, 93, 92],
        [11+24, 3+12, 0+12, 8+24], [9+84, 11+48, 7+48, 4+84],
        [9+84, 7+12, 3+12, 8+84], [32, 56, 55, 31],
        [11+48, 7+12, 0+12, 8+48], [4+84, 7+24, 11+24, 8+84]
    ],
    [
        # back top right (inner)
        [20, 58, 44], [21, 82, 45], [16, 57, 81], [53, 77, 40],
        [16, 21, 20], [40, 45, 44], [53, 58, 57], [77, 82, 81],
        [8+12, 8+36, 9+36, 9+12], [5+72, 5+48, 9+48, 9+72],
        [9+12, 10+72, 9+72, 4+12], [4+36, 5+48, 10+48, 8+36],
        [9+48, 4+12, 8+12, 10+48], [10+72, 9+36, 4+36, 5+72]
    ],
    [
        # back bottom left (inner)
        [23, 94, 47], [18, 71, 95], [22, 70, 46], [90, 66, 42],
        [18, 23, 22], [42, 47, 46], [66, 71, 70], [90, 95, 94],
        [10+12, 10+36, 11+36, 11+12], [6+84, 6+60, 11+60, 11+84],
        [11+84, 6+12, 11+12, 10+84], [6+36, 6+60, 10+60, 10+36],
        [10+12, 10+60, 11+60, 6+12], [10+84, 11+36, 6+36, 6+84]
    ],
    [
        # front top right (outer)
        [0, 24, 48], [1, 25, 72], [4, 49, 73], [28, 52, 76],
        [0, 1, 4], [72, 73, 76], [48, 49, 52], [24, 25, 28],
        [4+72, 4+48, 1+48, 1+72], [0, 1, 25, 24],
        [24, 48, 52, 28], [4, 1, 72, 73],
        [25, 72, 76, 28], [0, 4, 49, 48]
    ],
    [
        # front bottom left (outer)
        [3, 27, 84], [6, 63, 87], [30, 91, 67], [2, 26, 60],
        [2, 3, 6], [26, 27, 30], [63, 60, 67], [87, 84, 91],
        [7+84, 7+60, 3+60, 3+84], [2, 3, 27, 26],
        [67, 30, 26, 60], [6, 3, 84, 87],
        [7+84, 6+24, 3+24, 0+84], [2, 6, 63, 60]
    ],
    [
        # back top left (outer)
        [54, 89, 43], [11, 86, 39], [8, 50, 36], [7, 51, 85],
        [7, 8, 11], [39, 36, 43], [50, 51, 54], [85, 86, 89],
        [1+84, 3+48, 6+48, 5+84], [11, 8, 36, 39],
        [7+36, 6+48, 2+48, 0+36], [7, 11, 86, 85],
        [2+84, 3+36, 7+36, 5+84], [8, 7, 51, 50]
    ],
    [
        # back bottom right (outer)
        [10, 62, 38], [78, 65, 41], [5, 75, 61], [9, 74, 37],
        [5, 10, 9], [74, 75, 78], [61, 62, 65], [37, 38, 41],
        [3+72, 1+60, 5+60, 6+72], [9, 10, 38, 37],
        [5+36, 5+60, 2+60, 2+36], [5, 9, 74, 75],
        [2+72, 1+36, 5+36, 6+72], [10, 5, 61, 62]
    ]
]

Cubos1_Cols = [
    [5, 5, 5, 5, 3, 3, 3, 3, 0, 0, 1, 1, 2, 2] for cell in Cubos1_Cs
]

Cubos2_Cs = [
    [
        # front top right (inner)
        [12, 32, 56], [13, 33, 80], [16, 57, 81], [28, 52, 76],
        [12, 13, 16], [28, 33, 32], [52, 57, 56], [76, 81, 80],
        [0+12, 8+24, 9+24, 1+12], [9+48, 9+72, 4+72, 4+48],
        [9+72, 4+12, 1+12, 8+72], [52, 28, 32, 56],
        [0+12, 8+48, 9+48, 4+12], [76, 28, 33, 80]
    ],
    [
        # front bottom left (inner)
        [15, 35, 92], [18, 71, 95], [14, 34, 68], [30, 91, 67],
        [14, 15, 18], [30, 35, 34], [67, 68, 71], [91, 92, 95],
        [2+12, 10+24, 11+24, 3+12], [11+60, 11+84, 7+84, 7+60],
        [3+12, 8+84, 11+84, 6+12], [34, 68, 67, 30],
        [11+60, 6+12, 2+12, 8+60], [11+24, 8+84, 7+84, 6+24]
    ],
    [
        # back bottom right (inner)
        [22, 70, 46], [17, 83, 69], [21, 82, 45], [78, 65, 41],
        [17, 22, 21], [41, 46, 45], [65, 70, 69], [78, 83, 82],
        [9+36, 9+12, 10+12, 10+36], [5+60, 6+72, 11+72, 9+60],
        [11+72, 5+12, 9+12, 10+72], [10+60, 10+36, 5+36, 5+60],
        [9+60, 5+12, 10+12, 10+60], [5+36, 6+72, 10+72, 9+36]
    ],
    [
        # back top left (inner)
        [23, 94, 47], [20, 58, 44], [19, 59, 93], [54, 89, 43],
        [19, 20, 23], [43, 44, 47], [54, 59, 58], [89, 94, 93],
        [11+36, 11+12, 8+12, 8+36], [6+48, 5+84, 9+84, 11+48],
        [11+12, 10+84, 9+84, 7+12], [10+48, 8+36, 7+36, 6+48],
        [8+12, 10+48, 11+48, 7+12], [7+36, 5+84, 10+84, 11+36]
    ],
    [
        # front bottom right (outer)
        [2, 26, 60], [5, 75, 61], [29, 64, 79], [1, 25, 72],
        [1, 2, 5], [25, 26, 29], [60, 61, 64], [75, 72, 79],
        [4+60, 7+72, 3+72, 1+60], [1, 2, 26, 25],
        [26, 60, 64, 29], [1, 5, 75, 72],
        [79, 29, 25, 72], [5, 2, 60, 61]
    ],
    [
        # front top left (outer)
        [7, 51, 85], [31, 55, 88], [0, 24, 48], [3, 27, 84],
        [3, 0, 7], [27, 24, 31], [51, 48, 55], [84, 85, 88],
        [7+48, 4+84, 1+84, 3+48], [3, 0, 24, 27],
        [55, 31, 24, 48], [3, 7, 85, 84],
        [3+24, 0+84, 4+84, 7+24], [7, 0, 48, 51]
    ],
    [
        # back top right (outer)
        [8, 50, 36], [9, 74, 37], [53, 77, 40], [4, 49, 73],
        [4, 9, 8], [36, 37, 40], [49, 50, 53], [73, 74, 77],
        [1+48, 1+72, 5+72, 5+48], [8, 9, 37, 36],
        [2+48, 0+36, 4+36, 5+48], [9, 4, 73, 74],
        [4+36, 5+72, 2+72, 1+36], [4, 8, 50, 49]
    ],
    [
        # back bottom left (outer)
        [11, 86, 39], [90, 66, 42], [6, 63, 87], [10, 62, 38],
        [6, 11, 10], [38, 39, 42], [62, 63, 66], [86, 87, 90],
        [3+60, 3+84, 6+84, 6+60], [10, 11, 39, 38],
        [2+60, 2+36, 6+36, 6+60], [11, 6, 87, 86],
        [6+36, 6+84, 2+84, 3+36], [6, 10, 62, 63]
    ]
]

Cubos2_Cols = [
    [5, 5, 5, 5, 4, 4, 4, 4, 0, 0, 1, 1, 2, 2] for cell in Cubos1_Cs
]

Cells = [
    Cubos0_Cs, Cubos1_Cs, Cubos2_Cs,
    Cubes0_Cs, Cubes1_Cs, Cubes2_Cs
]
CellGroups = [
    'Cuboctahedra group 0', 'Cuboctahedra group 1', 'Cuboctahedra group 2',
    'Cube group 0', 'Cube group 1', 'Cube group 2'
]
ColGroups = [
    Cubos0_Cols, Cubos1_Cols, Cubos2_Cols,
    Cubes0_Cols, Cubes1_Cols, Cubes2_Cols
]

#FsOpaq =
#FsTransp_0 =  # Transparent Octahedra group 0
#FsTransp_1 =  # Transparent Octahedra group 1

Col0  = rgb.orange[:]
Col0.append(0.4)
Col1  = rgb.red[:]
Col1.append(0.4)
Col2  = rgb.yellow[:]
Col2.append(0.2)
Col3  = rgb.darkOliveGreen[:]
Col3.append(0.9)
Col4  = rgb.springGreen[:]
Col4.append(0.9)
#Col5  = rgb.sienna[:]
Col5  = rgb.royalBlue[:]
Col5.append(0.9)

Cols  = [Col0, Col1, Col2, Col3, Col4, Col5]

Es_0 = [
        0, 1, 1, 2, 2, 3, 3, 0, 8, 9, 9, 10, 10, 11, 11, 8,
        1, 5, 5, 9, 9, 4, 4, 1, 3, 7, 7, 11, 11, 6, 6, 3,
        0, 4, 4, 8, 8, 7, 7, 0, 2, 6, 6, 10, 10, 5, 5, 2,
    ]
offsetIndexWith = lambda i: lambda x: x+i
Es = []
Es.extend(list(map(offsetIndexWith(0), Es_0)))
Es.extend(list(map(offsetIndexWith(12), Es_0)))
Es.extend(list(map(offsetIndexWith(24), Es_0)))
Es.extend(list(map(offsetIndexWith(36), Es_0)))
Es.extend(list(map(offsetIndexWith(48), Es_0)))
Es.extend(list(map(offsetIndexWith(60), Es_0)))
Es.extend(list(map(offsetIndexWith(72), Es_0)))
Es.extend(list(map(offsetIndexWith(84), Es_0)))
Es.extend(
    [
        # triangle edges from shell of cubes inside outer shell:
        0, 24, 24, 48, 48, 0,
        1, 25, 25, 72, 72, 1,
        4, 49, 49, 73, 73, 4,
        28, 52, 52, 76, 76, 28,
        2, 26, 26, 60, 60, 2,
        5, 75, 75, 61, 61, 5,
        29, 64, 64, 79, 79, 29,
        3, 27, 27, 84, 84, 3,
        6, 63, 63, 87, 87, 6,
        30, 91, 91, 67, 67, 30,
        7, 51, 51, 85, 85, 7,
        31, 55, 55, 88, 88, 31,
        8, 50, 50, 36, 36, 8,
        9, 74, 74, 37, 37, 9,
        53, 77, 77, 40, 40, 53,
        10, 62, 62, 38, 38, 10,
        78, 65, 65, 41, 41, 78,
        11, 86, 86, 39, 39, 11,
        90, 66, 66, 42, 42, 90,
        54, 89, 89, 43, 43, 54,
        # triangles from first shell cubes on top of centre cube
        12, 32, 32, 56, 56, 12,
        13, 33, 33, 80, 80, 13,
        16, 57, 57, 81, 81, 16,
        14, 34, 34, 68, 68, 14,
        17, 83, 83, 69, 69, 17,
        15, 35, 35, 92, 92, 15,
        18, 71, 71, 95, 95, 18,
        19, 59, 59, 93, 93, 19,
        20, 58, 58, 44, 44, 20,
        21, 82, 82, 45, 45, 21,
        22, 70, 70, 46, 46, 22,
        23, 94, 94, 47, 47, 23,
    ]
)

class Shape(Geom4D.SimpleShape):
    def __init__(this):
        Cs = []
        cols = []
        assert len(Cells) == len(ColGroups)
        for i in range(len(Cells)):
            Cs.extend(Cells[i])
            cols.extend(ColGroups[i])
        Geom4D.SimpleShape.__init__(this,
            Vs, Cs = Cs, Es = Es, Ns = [],
            colors = (Cols, cols),
            name = TITLE
        )
        this.showGroup = [True for i in range(len(Cells))]
        this.showWhichCells = []
        for i in range(len(Cells)):
            this.showWhichCells.append([True for j in range(len(Cells[i]))])
        # On default, don't draw the outer cell:
        this.showWhichCells[0][-1] = False
        # For performance: don't show the cubes: all squares are shown by cubos
        for i in range(3, len(Cells)):
            this.showGroup[i] = False
        # tmp:
        #this.useTransparency(False)
        this.showFs()
        this.setProjectionProperties(wCameraDistance = 2.8, w_prj_vol = 1.0)

    def setShowGroup(this, groupId, show = True):
        this.showGroup[groupId] = show
        this.showFs()

    def setShowCellsOfGroup(this, groupId, cellList):
        this.showWhichCells[groupId] = cellList
        if this.showGroup[groupId]:
            this.showFs()

    def showFs(this):
        Cs = []
        colIds = []
        for i in range(len(Cells)):
            if this.showGroup[i]:
                for j in range(len(this.showWhichCells[i])):
                    if this.showWhichCells[i][j]:
                        Cs.append(Cells[i][j])
                        colIds.append(ColGroups[i][j])
                    else:
                        Cs.append([])
                        colIds.append([])
        this.setCellProperties(Cs = Cs)
        this.setFaceProperties(colors = (Cols, colIds))

    def gl_init(self):
        super().gl_init()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        this.shape = shape
        this.canvas = canvas
        kwargs['title'] = TITLE
        wx.Frame.__init__(this, *args, **kwargs)
        this.panel = wx.Panel(this, -1)
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.mainSizer.Add(
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.set_default_size((475, 550))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

    def createControlsSizer(this):
        ctrlSizer = wx.BoxSizer(wx.VERTICAL)

        str = 'cell %d'
        lenR = 2*len(str) + 1
        r2 = list(range(2))
        lenL = [0 for j in r2]
        nrOfCellsInColumn = len(Cells) // 2
        for i in range(nrOfCellsInColumn):
            for j in r2:
                lenL[j] = max(lenL[j], 2*len(CellGroups[nrOfCellsInColumn * j + i]))
        this.showGui = []
        showFacesSizer = wx.StaticBoxSizer(
            wx.StaticBox(this.panel, label = 'View Settings'),
            wx.HORIZONTAL
        )
        columnSizer = [wx.BoxSizer(wx.VERTICAL) for j in r2]
        L = [0 for j in r2]
        for j in r2:
            for i in range(nrOfCellsInColumn):
                cellIndex = nrOfCellsInColumn * j + i
                showWhich = this.shape.showWhichCells[cellIndex]
                l = len(showWhich)
                cellList = [ str % k for k in range(l)]
                this.showGui.append(wx.CheckBox(this.panel, label = CellGroups[cellIndex] + ':'))
                this.showGui[-1].SetValue(this.shape.showGroup[cellIndex])
                this.showGui[-1].Bind(wx.EVT_CHECKBOX,
                    this.onShowGroup,
                    id = this.showGui[-1].GetId()
                )
                this.showGui.append(wx.CheckListBox(this.panel, choices = cellList))
                this.showGui[-1].Bind(wx.EVT_CHECKLISTBOX,
                    this.onShowCells,
                    id = this.showGui[-1].GetId()
                )
                for k in range(l):
                    this.showGui[-1].Check(k ,showWhich[k])
                showCellsSizer = wx.BoxSizer(wx.HORIZONTAL)
                showCellsSizer.Add(this.showGui[-2], lenL[j], wx.EXPAND)
                showCellsSizer.Add(this.showGui[-1], lenR, wx.EXPAND)
                columnSizer[j].Add(showCellsSizer, 2*l+1, wx.EXPAND)
                L[j] += l

        Lmax = 0
        for j in r2:
            Lmax = max(Lmax, L[j])
            showFacesSizer.Add(columnSizer[j], lenR + lenL[j], wx.EXPAND)
        ctrlSizer.Add(showFacesSizer, Lmax, wx.EXPAND)
        return ctrlSizer

    def onShowGroup(this, event):
        for i in range(0, len(this.showGui), 2):
            if this.showGui[i].GetId() == event.GetId():
                this.shape.setShowGroup(i//2, this.showGui[i].IsChecked())
        logging.info(
            f"Ctrl Window size: ({this.GetClientSize()[0]}, {this.GetClientSize()[1]})"
        )
        this.canvas.paint()

    def onShowCells(this, event):
        for i in range(1, len(this.showGui), 2):
            if this.showGui[i].GetId() == event.GetId():
                this.showGui[i].SetSelection(event.GetSelection())
                groupId = i//2 # actually it should be (i-1)/2 but rounding fixes this
                list = [ this.showGui[i].IsChecked(j) for j in range(len(Cells[groupId])) ]
                this.shape.setShowCellsOfGroup(groupId, list)
        this.canvas.paint()

    # move to general class
    def set_default_size(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
