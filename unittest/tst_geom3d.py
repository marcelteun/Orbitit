#!/usr/bin/env python
"""Test geom3D."""
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
from os import path
import unittest

import Geom3D
import geomtypes

red = (.8, .1, .1)
yellow = (.8, .8, .3)
DIR = "unittest"


def get_cube():
    Vs = [geomtypes.Vec3([ 1,  1,  1]),
          geomtypes.Vec3([-1,  1,  1]),
          geomtypes.Vec3([-1, -1,  1]),
          geomtypes.Vec3([ 1, -1,  1]),
          geomtypes.Vec3([ 1,  1, -1]),
          geomtypes.Vec3([-1,  1, -1]),
          geomtypes.Vec3([-1, -1, -1]),
          geomtypes.Vec3([ 1, -1, -1]),
          geomtypes.Vec3([ 1,  1, -2]),
          geomtypes.Vec3([.5,  1,  1])]
    Fs = [[0, 1, 2, 3],
          [0, 3, 7, 4],
          [1, 0, 4, 5],
          [2, 1, 5, 6],
          [3, 2, 6, 7],
          [7, 6, 5, 4]]
    return Geom3D.SimpleShape(Vs=Vs, Fs=Fs,
                              colors=([red], []))


def get_octahedron():
    Vs = [geomtypes.Vec3([ 0,  0,  2]),
          geomtypes.Vec3([ 2,  0,  0]),
          geomtypes.Vec3([ 0,  2,  0]),
          geomtypes.Vec3([-2,  0,  0]),
          geomtypes.Vec3([ 0, -2,  0]),
          geomtypes.Vec3([ 0,  0, -2])]
    Fs = [[0, 1, 2],
          [0, 2, 3],
          [0, 3, 4],
          [0, 4, 1],
          [5, 2, 1],
          [5, 3, 2],
          [5, 4, 3],
          [5, 1, 4]]
    return Geom3D.SimpleShape(Vs=Vs, Fs=Fs,
                              colors=([yellow], []))


def get_path(filename):
    """Return path to test file to compare with"""
    return path.join(DIR, filename)


class TestSimpleShape(unittest.TestCase):
    """Unit tests for Geom3D.CompoundShape"""
    shape = get_cube()
    name = "simple_shape"

    def test_export_to_ps(self):
        tst_str = self.shape.toPsPiecesStr()
        org = get_path(self.name + ".ps")
        with open(org, 'r') as fd:
            org_str = fd.read()
        if tst_str != org_str:
            with open(org + '.diff', 'w') as fd:
                fd.write(tst_str)
        self.assertEqual(tst_str, org_str)

    def test_export_to_off(self):
        tst_str = self.shape.toOffStr()
        org = get_path(self.name + ".off")
        with open(org, 'r') as fd:
            org_str = fd.read()
        self.assertEqual(tst_str, org_str)

    def test_repr(self):
        tst_str = repr(self.shape)
        org = get_path(self.name + ".repr")
        with open(org, 'r') as fd:
            org_str = fd.read()
        self.assertEqual(tst_str, org_str)


class TestCompoundShape(TestSimpleShape):
    """Unit tests for Geom3D.CompoundShape"""
    shape = Geom3D.CompoundShape([get_cube(), get_octahedron()])
    name = "compound_shape"


if __name__ == '__main__':
    unittest.main()
