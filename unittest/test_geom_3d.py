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

from orbitit import geom_3d, geomtypes, isometry

RED = (.8, .1, .1)
YELLOW = (.8, .8, .3)
BLUE = (.3, .3, .8)

DIR_PATH = path.dirname(path.realpath(__file__))
OUT_DIR = "output"
IN_DIR = "expected"


def get_cube():
    """Return a shape describing one cube"""
    vs = [geomtypes.Vec3([ 1,  1,  1]),
          geomtypes.Vec3([-1,  1,  1]),
          geomtypes.Vec3([-1, -1,  1]),
          geomtypes.Vec3([ 1, -1,  1]),
          geomtypes.Vec3([ 1,  1, -1]),
          geomtypes.Vec3([-1,  1, -1]),
          geomtypes.Vec3([-1, -1, -1]),
          geomtypes.Vec3([ 1, -1, -1]),
          geomtypes.Vec3([ 1,  1, -2]),
          geomtypes.Vec3([.5,  1,  1])]
    fs = [[0, 1, 2, 3],
          [0, 3, 7, 4],
          [1, 0, 4, 5],
          [2, 1, 5, 6],
          [3, 2, 6, 7],
          [7, 6, 5, 4]]
    return geom_3d.SimpleShape(vs=vs, fs=fs,
                              colors=([RED, YELLOW, BLUE], [0, 1, 2, 1, 2, 0]))


def get_octahedron():
    """Return a shape describing one octahedron"""
    vs = [geomtypes.Vec3([ 0,  0,  2]),
          geomtypes.Vec3([ 2,  0,  0]),
          geomtypes.Vec3([ 0,  2,  0]),
          geomtypes.Vec3([-2,  0,  0]),
          geomtypes.Vec3([ 0, -2,  0]),
          geomtypes.Vec3([ 0,  0, -2])]
    fs = [[0, 1, 2],
          [0, 2, 3],
          [0, 3, 4],
          [0, 4, 1],
          [5, 2, 1],
          [5, 3, 2],
          [5, 4, 3],
          [5, 1, 4]]
    return geom_3d.SimpleShape(vs=vs, fs=fs,
                              colors=([YELLOW], []))


def get_path(filename, sub_dir):
    """Return path to test-file to compare with"""
    return path.join(DIR_PATH, sub_dir, filename)


def chk_with_org(filename, chk_str):
    """Get file contents from file with expected data"""
    org_name = get_path(filename, IN_DIR)
    chk_name = get_path(filename + '.chk', OUT_DIR)
    try:
        with open(org_name, 'r') as fd:
            expect_str = fd.read()
    except IOError:
        with open(chk_name, 'w') as fd:
            fd.write(chk_str)
        return (False, f"Missing file, check {org_name}")
    if chk_str != expect_str:
        with open(chk_name, 'w') as fd:
            fd.write(chk_str)
        return (False, f"Unexpected content {chk_name} != {org_name} (expected)")
    return (True, "")


class TestLine(unittest.TestCase):
    """Unit tests for geom_3d.Line3D"""
    def test_intersections(self):
        """Test line intersections, using line within a cube."""
        test_matrix = {
            "edges_meet_at_vertex": [
                # Lines
                [
                    geom_3d.Line3D([1, 1, 1], [0, 1, 1]),
                    geom_3d.Line3D([-1, -1, 1], [-1, 0, 1]),
                ],
                # Expected result
                geomtypes.Vec3([-1, 1, 1]),
            ]
        }
        for test_name, (lines, expected_result) in test_matrix.items():
            result = lines[0].intersect(lines[1])
            if not result == expected_result:
                self.fail(
                    f"{result} != {expected_result} (expected) for {test_name}"
                )


class TestFace(unittest.TestCase):

    def test_face_shapes(self):
        test_matrix = {
            "square": {
                "vs": [
                    geomtypes.Vec3([4, 0, 0]),
                    geomtypes.Vec3([0, 4, 0]),
                    geomtypes.Vec3([-4, 0, 0]),
                    geomtypes.Vec3([0, -4, 0]),
                ],
                "expected": {
                    "gravity": geomtypes.Vec3([0, 0, 0]),
                    "first_vec": geomtypes.Vec3([1, 0, 0]),
                    "normal": geomtypes.Vec3([0, 0, 1]),
                    "angles_deg": [0, 90, 180, 270],
                    "with_concave_points": [
                        geomtypes.Vec3([4, 0, 0]),
                        geomtypes.Vec3([0, 4, 0]),
                        geomtypes.Vec3([-4, 0, 0]),
                        geomtypes.Vec3([0, -4, 0]),
                    ],
                },
            },
            "5-star": {  # a star with concave points between all vertices (using ints)
                "vs": [
                    geomtypes.Vec3([1, 2, 2]),
                    geomtypes.Vec3([1, 14, 8]),
                    geomtypes.Vec3([1, 2, 8]),
                    geomtypes.Vec3([1, 10, 0]),
                    geomtypes.Vec3([1, 10, 18]),
                ],
                "expected": {
                    "gravity": geomtypes.Vec3([1, 7.6, 7.2]),
                    "first_vec": geomtypes.Vec3([0, -5.6, -5.2]).normalise(),
                    "normal": geomtypes.Vec3([1, 0, 0]),
                    "angles_deg": None,  # skip
                    "with_concave_points": [
                        geomtypes.Vec3([1, 2, 2]),
                        geomtypes.Vec3([1, 6, 4]),
                        geomtypes.Vec3([1, 10, 0]),
                        geomtypes.Vec3([1, 10, 6]),
                        geomtypes.Vec3([1, 14, 8]),
                        geomtypes.Vec3([1, 10, 8]),
                        geomtypes.Vec3([1, 10, 18]),
                        geomtypes.Vec3([1, 5, 8]),
                        geomtypes.Vec3([1, 2, 8]),
                        geomtypes.Vec3([1, 4, 6]),
                    ],
                },
            },
            "bowtie": {  # a bowtie: mixes concave points and no concave points
                "vs": [
                    geomtypes.Vec3([1, 0, 1]),
                    geomtypes.Vec3([3, 2, 1]),
                    geomtypes.Vec3([1, 2, 1]),
                    geomtypes.Vec3([3, 0, 1]),
                ],
                "expected": {
                    "gravity": geomtypes.Vec3([2, 1, 1]),
                    "first_vec": geomtypes.Vec3([-1, -1, 0]).normalise(),
                    "normal": geomtypes.Vec3([0, 0, -1]),
                    "angles_deg": [0, 180, 90, 270],
                    "with_concave_points": [
                        geomtypes.Vec3([1, 0, 1]),
                        geomtypes.Vec3([2, 1, 1]),
                        geomtypes.Vec3([1, 2, 1]),
                        geomtypes.Vec3([3, 2, 1]),
                        geomtypes.Vec3([2, 1, 1]),
                        geomtypes.Vec3([3, 0, 1]),
                    ],
                },
            },
        }
        for test_case, test_data in test_matrix.items():
            vs = test_data["vs"]
            expected = test_data["expected"]
            test_face = geom_3d.Face(vs)

            # Test gravity attribute
            self.assertEqual(
                test_face.gravity,
                expected["gravity"],
                f"while testing gravity for {test_case}",
            )

            # Test first_vac attribute
            self.assertEqual(
                test_face.first_vec,
                expected["first_vec"],
                f"while testing first_vec for {test_case}",
            )

            # Test normal attribute
            self.assertEqual(
                test_face.normal(normalise=True),
                expected["normal"],
                f"while testing normal for {test_case}",
            )

            # Test angles attribute
            expected_angles = expected["angles_deg"]
            if expected_angles:
                result = test_face.angles
                self.assertEqual(len(result), len(expected_angles), f"while testing {test_case}")
                for i, (expected_angle, angle) in enumerate(zip(expected_angles, result)):
                    self.assertEqual(
                        angle / geom_3d.DEG2RAD,
                        expected_angle,
                        f"while testing angles for {test_case}, angle #{i}",
                    )

            # Test len, iter and with_concave_points attribute
            result = test_face.with_concave_points
            self.assertEqual(
                len(result),
                len(expected["with_concave_points"]),
                f"while testing amount of concave points for {test_case}",
            )
            errors = []
            for i, (expected_point, point) in enumerate(
                zip(expected["with_concave_points"], result)
            ):
                if point != expected_point:
                    errors.append(i)
            if errors:
                error_str = f"Unexpected result while testing concave points for {test_case}:\n"
                result_str = "["
                expected_str = "["
                for i, (expected_point, point) in enumerate(
                    zip(expected["with_concave_points"], result)
                ):
                    result_str += f"  {i}. {point}\n"
                    expected_str += f"  {i}. {expected_point}\n"
                result_str += "]"
                expected_str += "]"
                error_str += f"{result_str} !=\n{expected_str} (expected)\n for {errors}"
                self.fail(error_str)


class TestSimpleShape(unittest.TestCase):
    """Unit tests for geom_3d.SimpleShape"""
    shape = None
    name = "simple_shape"
    ps_margin = 10
    ps_precision = 7
    scale = 1

    def def_shape(self):
        """Define shape"""
        self.shape = get_cube()

    def ensure_shape(self):
        """Make sure the shape is defined"""
        if not self.shape:
            self.def_shape()

    def test_export_to_ps(self):
        """Test export to PostScript function"""
        self.ensure_shape()
        with geomtypes.FloatHandler(self.ps_margin):
            tst_str = self.shape.to_postscript(
                scaling=self.scale,
                precision=self.ps_precision,
            )
        result, msg = chk_with_org(self.name + ".ps", tst_str)
        self.assertTrue(result, msg)

    def test_export_to_off(self):
        """Test export to off-format function"""
        self.ensure_shape()
        tst_str = self.shape.to_off(precision=15)
        result, msg = chk_with_org(self.name + ".off", tst_str)
        self.assertTrue(result, msg)

    def test_export_to_json(self):
        """Test export to JSON file format."""
        self.ensure_shape()
        with geomtypes.FloatHandler(12):
            tst_str = self.shape.json_str
        result, msg = chk_with_org(self.name + ".json", tst_str)
        self.assertTrue(result, msg)

    def test_repr(self):
        """Test repr-format function"""
        self.ensure_shape()
        with geomtypes.FloatHandler(12):
            tst_str = repr(self.shape)
        result, msg = chk_with_org(self.name + ".repr", tst_str)
        self.assertTrue(result, msg)


class TestSimpleShapeExtended(TestSimpleShape):
    """Unit tests for geom_3d.SimpleShape"""

    def test_scale(self):
        """Test scale and export to off-format"""
        self.ensure_shape()
        self.shape.scale(2)
        tst_str = self.shape.to_off(precision=15)
        result, msg = chk_with_org("scaled_" + self.name + ".off", tst_str)
        self.assertTrue(result, msg)
        self.shape = None

    def test_rotate(self):
        """Test scale and export to off-format"""
        self.ensure_shape()
        self.shape.transform(geomtypes.Rot3(angle=0.3, axis=geomtypes.Vec3([1, 2, 3])))
        tst_str = self.shape.to_off(precision=15)
        result, msg = chk_with_org("rotated_" + self.name + ".off", tst_str)
        self.assertTrue(result, msg)
        self.shape = None


class TestCompoundShape(TestSimpleShapeExtended):
    """Unit tests for geom_3d.CompoundShape"""
    ps_margin = 6
    name = "compound_shape"

    def def_shape(self):
        """Define shape"""
        self.shape = geom_3d.CompoundShape([get_cube(), get_octahedron()], "abc")


class TestSymmetricShape(TestSimpleShapeExtended):
    """Unit test for geom_3d.SymmetricShape"""
    shape = None
    name = "isom_12cubes"
    scale = 50

    def def_shape(self):
        """Define an SymmetricShape describing a compound of 12 cubes

        The descriptive doesn't use the default orientation
        """
        v2_div_2 = math.sqrt(2) / 2
        self.shape = geom_3d.SymmetricShape(
            vs=[geomtypes.Vec3([1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, -1.0, -1.0]),
                geomtypes.Vec3([1.0, -1.0, -1.0])],
            fs=[[0, 1, 2, 3],
                [0, 3, 7, 4],
                [1, 0, 4, 5],
                [2, 1, 5, 6],
                [3, 2, 6, 7],
                [7, 6, 5, 4]],
            es=[0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6, 2,
                6, 6, 7],
            colors=[
                [0.996094, 0.839844, 0.0],
                [0.132812, 0.542969, 0.132812],
                [0.542969, 0.0, 0.0],
                [0.0, 0.746094, 0.996094],
                [0.542969, 0.0, 0.0],
                [0.132812, 0.542969, 0.132812],
                [0.0, 0.746094, 0.996094],
                [0.0, 0.746094, 0.996094],
                [0.996094, 0.839844, 0.0],
                [0.542969, 0.0, 0.0],
                [0.132812, 0.542969, 0.132812],
                [0.996094, 0.839844, 0.0],
            ],
            isometries=[
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
            name=self.name,
            orientation=geomtypes.Rot3((
                geomtypes.Quat([0.953020613871,
                                0.214186495298,
                                0.0,
                                0.214186495298]),
                geomtypes.Quat([0.953020613871,
                                -0.214186495298,
                                0.0,
                                -0.214186495298])))
        )
        # for debugging:
        #self.shape.json_indent = 2


class TestSymmetricShape1(TestSimpleShapeExtended):
    """More unit test for geom_3d.SymmetricShape"""
    shape = None
    name = "isom_5cubes"
    scale = 50

    def def_shape(self):
        """Define an SymmetricShape describing a compound of 5 cubes

        The descriptive uses the default orientation
        """
        a = 0.809016994375
        b = 0.309016994375
        self.shape = geom_3d.SymmetricShape(
            vs=[geomtypes.Vec3([1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, -1.0, -1.0]),
                geomtypes.Vec3([1.0, -1.0, -1.0])],
            fs=[[0, 1, 2, 3],
                [0, 3, 7, 4],
                [1, 0, 4, 5],
                [2, 1, 5, 6],
                [3, 2, 6, 7],
                [7, 6, 5, 4]],
            es=[0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6,
                2, 6, 6, 7],
            colors=[
                [0.996094, 0.839844, 0.0],
                [0.132812, 0.542969, 0.132812],
                [0.542969, 0.0, 0.0],
                [0.0, 0.746094, 0.996094],
                [0.542969, 0.523438, 0.304688],
            ],
            isometries=[
                geomtypes.Rot3((geomtypes.Quat([-a, -0.5, b, 0]),
                                geomtypes.Quat([-a, 0.5, -b, 0]))),
                geomtypes.Rot3((geomtypes.Quat([a, -b, 0, -0.5]),
                                geomtypes.Quat([a, b, 0, 0.5]))),
                geomtypes.Rot3((geomtypes.Quat([0.5, 0.5, -0.5, -0.5]),
                                geomtypes.Quat([0.5, -0.5, 0.5, 0.5]))),
                geomtypes.Rot3((geomtypes.Quat([0.5, 0, -b, a]),
                                geomtypes.Quat([0.5, 0, b, -a]))),
                geomtypes.Rot3((geomtypes.Quat([0, -0.5, a, b]),
                                geomtypes.Quat([0, 0.5, -a, -b])))
            ],
            name=self.name,
            orientation=geomtypes.Rot3((geomtypes.Quat([1.0, 0.0, 0.0, 0.0]),
                                        geomtypes.Quat([1.0, 0.0, 0.0, 0.0])))
        )
        # for debugging:
        #self.shape.json_indent = 2

class TestSymmetricShapeDifferentIsometries1(TestSimpleShapeExtended):
    """More unit test for geom_3d.SymmetricShape with different isometries.

    Different isometries as in reflections, rotary inversion.
    """
    shape = None
    name = "different_isoms"
    scale = 50

    def def_shape(self):
        """Define an SymmetricShape consisting of irregular tetrahedra

        The descriptive uses the default orientation
        """
        self.shape = geom_3d.SymmetricShape(
            vs=[geomtypes.Vec3([1.0, -0.5, 1.0]),
                geomtypes.Vec3([-1.0, 1.0, 1.0]),
                geomtypes.Vec3([1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, -1.0, -1.0]),
            ],
            fs=[
                [0, 2, 1],
                [0, 1, 3],
                [0, 3, 2],
                [1, 2, 3],
            ],
            colors=[
                [0.996094, 0.839844, 0.0],
                [0.132812, 0.542969, 0.132812],
                [0.542969, 0.0, 0.0],
            ],
            isometries=[
                geomtypes.Rot3(angle=0, axis=geomtypes.Vec3([1, 0, 0])),
                geomtypes.Refl3(normal=geomtypes.Vec3([1, 0, 0])),
                geomtypes.RotInv3(angle=2*math.pi/3, axis=geomtypes.Vec3([-1, 1, 1])),
            ],
            name=self.name,
            #orientation=geomtypes.Rot3(angle=math.pi/4, axis=geomtypes.Vec3([0, 0, 1]))
        )
        # for debugging:
        #self.shape.json_indent = 2

class TstSymmetricShapeDifferentIsometries2(TestSymmetricShapeDifferentIsometries1):
    """More unit test for geom_3d.SymmetricShape with different isometries.

    Different isometries as in reflections, rotary inversion.
    """
    shape = None
    name = "different_isoms2"
    scale = 50

    def def_shape(self):
        """Define an SymmetricShape consisting of irregular tetrahedra

        The descriptive doesn't use the default orientation
        """
        super().def_shape()
        self.shape.orientation = geomtypes.Rot3(angle=math.pi/4, axis=geomtypes.Vec3([0, 0, 1]))
        self.shape.name = self.name
        # for debugging:
        #self.shape.json_indent = 2

class TestOrbitShape(TestSimpleShapeExtended):
    """More unit test for geom_3d.OrbitShape"""
    shape = None
    name = "orbit_5cubes"
    scale = 50

    def def_shape(self):
        """Define an OrbitShape describing a compound of 5 cubes

        The descriptive uses the default orientation
        """
        self.shape = geom_3d.OrbitShape(
            vs=[geomtypes.Vec3([1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, -1.0, -1.0]),
                geomtypes.Vec3([1.0, -1.0, -1.0])],
            fs=[[0, 1, 2, 3],
                [0, 3, 7, 4],
                [1, 0, 4, 5],
                [2, 1, 5, 6],
                [3, 2, 6, 7],
                [7, 6, 5, 4]],
            es=[0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6,
                2, 6, 6, 7],
            colors=[
                [0.996094, 0.839844, 0.0],
                [0.132812, 0.542969, 0.132812],
                [0.542969, 0.0, 0.0],
                [0.0, 0.746094, 0.996094],
                [0.542969, 0.523438, 0.304688],
            ],
            final_sym=isometry.A5(),
            stab_sym=isometry.A4(),
            name=self.name,
        )
        # for debugging:
        #self.shape.json_indent = 2


if __name__ == '__main__':
    unittest.main()
