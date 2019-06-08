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
import math
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


def cube_compound():
    v2_div_2 = math.sqrt(2) / 2
    return Geom3D.IsometricShape(
        Vs=[
            geomtypes.Vec3([1.0, 1.0, 1.0]),
            geomtypes.Vec3([-1.0, 1.0, 1.0]),
            geomtypes.Vec3([-1.0, -1.0, 1.0]),
            geomtypes.Vec3([1.0, -1.0, 1.0]),
            geomtypes.Vec3([1.0, 1.0, -1.0]),
            geomtypes.Vec3([-1.0, 1.0, -1.0]),
            geomtypes.Vec3([-1.0, -1.0, -1.0]),
            geomtypes.Vec3([1.0, -1.0, -1.0]),
        ],
        Fs=[
            [0, 1, 2, 3],
            [0, 3, 7, 4],
            [1, 0, 4, 5],
            [2, 1, 5, 6],
            [3, 2, 6, 7],
            [7, 6, 5, 4],
        ],
        Es=[0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6, 2, 6,
            6, 7],
        colors=[
            ([[0.996094, 0.839844, 0.0]], []),
            ([[0.132812, 0.542969, 0.132812]], []),
            ([[0.542969, 0.0, 0.0]], []),
            ([[0.0, 0.746094, 0.996094]], []),
            ([[0.542969, 0.0, 0.0]], []),
            ([[0.132812, 0.542969, 0.132812]], []),
            ([[0.0, 0.746094, 0.996094]], []),
            ([[0.0, 0.746094, 0.996094]], []),
            ([[0.996094, 0.839844, 0.0]], []),
            ([[0.542969, 0.0, 0.0]], []),
            ([[0.132812, 0.542969, 0.132812]], []),
            ([[0.996094, 0.839844, 0.0]], []),
        ],
        directIsometries=[
            geomtypes.Rot3((geomtypes.Quat([-0.5, 0.5, -0.5, -0.5]),
                            geomtypes.Quat([-0.5, -0.5, 0.5, 0.5]))),
            geomtypes.Rot3((geomtypes.Quat([-v2_div_2, 0, -v2_div_2, 0]),
                            geomtypes.Quat([-v2_div_2, 0, v2_div_2, 0]))),
            geomtypes.Rot3((geomtypes.Quat([0, 0, -v2_div_2, -v2_div_2]),
                            geomtypes.Quat([0, 0, v2_div_2, v2_div_2]))),
            geomtypes.Rot3((geomtypes.Quat([v2_div_2, -v2_div_2, 0, 0]),
                            geomtypes.Quat([v2_div_2, v2_div_2, 0, 0]))),
            geomtypes.Rot3((geomtypes.Quat([0, -v2_div_2, v2_div_2, 0]),
                            geomtypes.Quat([0, v2_div_2, -v2_div_2, 0]))),
            geomtypes.Rot3((geomtypes.Quat([0.5, -0.5, -0.5, -0.5]),
                            geomtypes.Quat([0.5, 0.5, 0.5, 0.5]))),
            geomtypes.Rot3((geomtypes.Quat([-0.5, -0.5, 0.5, -0.5]),
                            geomtypes.Quat([-0.5, 0.5, -0.5, 0.5]))),
            geomtypes.Rot3((geomtypes.Quat([0, v2_div_2, 0, -v2_div_2]),
                            geomtypes.Quat([0, -v2_div_2, 0, v2_div_2]))),
            geomtypes.Rot3((geomtypes.Quat([-v2_div_2, -v2_div_2, 0, 0]),
                            geomtypes.Quat([-v2_div_2, v2_div_2, 0, 0]))),
            geomtypes.Rot3((geomtypes.Quat([0, v2_div_2, 0, v2_div_2]),
                            geomtypes.Quat([0, -v2_div_2, 0, -v2_div_2]))),
            geomtypes.Rot3((geomtypes.Quat([0, 0, -v2_div_2, v2_div_2]),
                            geomtypes.Quat([0, 0, v2_div_2, -v2_div_2]))),
            geomtypes.Rot3((geomtypes.Quat([v2_div_2, 0, -v2_div_2, 0]),
                            geomtypes.Quat([v2_div_2, 0, v2_div_2, 0]))),
        ],
        unfoldOrbit=False,
        name="12cubes",
        orientation=geomtypes.Rot3((
            geomtypes.Quat([0.953020613871, 0.214186495298, 0.0, 0.214186495298]),
            geomtypes.Quat([0.953020613871, -0.214186495298, -0.0, -0.214186495298])))
        )


def get_path(filename):
    """Return path to test file to compare with"""
    return path.join(DIR, filename)


def write_chk_file(f, s):
    """Write a check file for filename 'f' string 's'"""
    with open(f + '.check', 'w') as fd:
        fd.write(s)


class TestSimpleShape(unittest.TestCase):
    """Unit tests for Geom3D.CompoundShape"""
    shape = get_cube()
    name = "simple_shape"
    scale = 1

    def chk_with_org(self, org, chk_str):
        """Get file contents from file with expected data"""
        try:
            with open(org, 'r') as fd:
                expect_str = fd.read()
        except IOError:
            write_chk_file(org, chk_str)
            self.assertTrue(False, 'Missing file, check {}'.format(org))
        if chk_str != expect_str:
            chk_file = org + '.chk'
            with open(chk_file, 'w') as fd:
                fd.write(chk_str)
            self.assertTrue(False, 'Unexpected content {} != {}'.format(
                org, chk_file))

    def test_export_to_ps(self):
        tst_str = self.shape.toPsPiecesStr(scaling=self.scale)
        org = get_path(self.name + ".ps")
        self.chk_with_org(org, tst_str)

    def test_export_to_off(self):
        tst_str = self.shape.toOffStr()
        org = get_path(self.name + ".off")
        self.chk_with_org(org, tst_str)

    def test_repr(self):
        tst_str = repr(self.shape)
        org = get_path(self.name + ".repr")
        self.chk_with_org(org, tst_str)


class TestCompoundShape(TestSimpleShape):
    """Unit tests for Geom3D.CompoundShape"""
    shape = Geom3D.CompoundShape([get_cube(), get_octahedron()])
    name = "compound_shape"


class TestIsometricShape(TestSimpleShape):
    """Unit tests for Geom3D.IsometricShape"""
    shape = cube_compound()
    name = "isometric_shape"
    scale = 50


if __name__ == '__main__':
    unittest.main()
