#!/usr/bin/env python
"""Test geom3D which takes more time"""
#
# Copyright (C) 2019 Marcel Tunnissen
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
# MERCHANTABILITY or FITNESS FOR a PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not,
# check at http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# or write to the Free Software Foundation,
#
# ------------------------------------------------------------------
# Since these tests are quite straight forward tests, and thers is no gain to
# split the methods and the file other than to shut up pylint:
# pylint: disable=too-many-lines,too-many-statements,too-many-locals
import unittest

import Geom3D
from tst_geom3d import get_path, TestSimpleShape

red = (.8, .1, .1)
yellow = (.8, .8, .3)
DIR = "unittest"


class TestUniformShape1(TestSimpleShape):
    """Unit tests for complex uniform shape imported as off-file"""
    shape = None
    name = "MW115"
    scale = 50
    ps_margin = 9
    ps_precision = 12

    def def_shape(self):
        name = get_path(self.name + ".off")
        with open(name, 'r') as fd:
            self.shape = Geom3D.readOffFile(fd, recreateEdges=True)


class TestUniformShape2(TestUniformShape1):
    """Unit tests for another complex uniform shape imported as off-file"""
    shape = None
    name = "MW117"


class TestUniformShape3(TestUniformShape1):
    """Unit tests for yet another complex uniform shape imported as off-file"""
    shape = None
    name = "MW119"
    scale = 50
    ps_margin = 9
    ps_precision = 11


if __name__ == '__main__':
    unittest.main()
