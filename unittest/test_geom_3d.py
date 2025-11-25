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
# pylint: disable=too-many-lines,too-many-statements,too-many-locals,too-many-branches
import math
from os import path
import unittest

from orbitit import geom_3d, geomtypes, isometry, orbit, rgb

RED = (0.8, 0.1, 0.1)
YELLOW = (0.8, 0.8, 0.3)
BLUE = (0.3, 0.3, 0.8)

DIR_PATH = path.dirname(path.realpath(__file__))
OUT_DIR = "output"
IN_DIR = "expected"


def get_cube():
    """Return a shape describing one cube"""
    vs = [
        geomtypes.Vec3([1, 1, 1]),
        geomtypes.Vec3([-1, 1, 1]),
        geomtypes.Vec3([-1, -1, 1]),
        geomtypes.Vec3([1, -1, 1]),
        geomtypes.Vec3([1, 1, -1]),
        geomtypes.Vec3([-1, 1, -1]),
        geomtypes.Vec3([-1, -1, -1]),
        geomtypes.Vec3([1, -1, -1]),
        geomtypes.Vec3([1, 1, -2]),
        geomtypes.Vec3([0.5, 1, 1]),
    ]
    fs = [
        [0, 1, 2, 3],
        [0, 3, 7, 4],
        [1, 0, 4, 5],
        [2, 1, 5, 6],
        [3, 2, 6, 7],
        [7, 6, 5, 4],
    ]
    return geom_3d.SimpleShape(
        vs=vs, fs=fs, colors=([RED, YELLOW, BLUE], [0, 1, 2, 1, 2, 0])
    )


def get_octahedron():
    """Return a shape describing one octahedron"""
    vs = [
        geomtypes.Vec3([0, 0, 2]),
        geomtypes.Vec3([2, 0, 0]),
        geomtypes.Vec3([0, 2, 0]),
        geomtypes.Vec3([-2, 0, 0]),
        geomtypes.Vec3([0, -2, 0]),
        geomtypes.Vec3([0, 0, -2]),
    ]
    fs = [
        [0, 1, 2],
        [0, 2, 3],
        [0, 3, 4],
        [0, 4, 1],
        [5, 2, 1],
        [5, 3, 2],
        [5, 4, 3],
        [5, 1, 4],
    ]
    return geom_3d.SimpleShape(vs=vs, fs=fs, colors=([YELLOW], []))


def get_tetrahedron():
    """Return a shape describing one octahedron"""
    vs = [
        geomtypes.Vec3([1, 1, 1]),
        geomtypes.Vec3([-1, -1, 1]),
        geomtypes.Vec3([1, -1, -1]),
        geomtypes.Vec3([-1, 1, -1]),
    ]
    fs = [
        [0, 1, 2],
        [0, 3, 1],
        [2, 3, 0],
        [1, 3, 2],
    ]
    return geom_3d.SimpleShape(vs=vs, fs=fs, colors=([YELLOW], []))


def get_path(filename, sub_dir):
    """Return path to test-file to compare with"""
    return path.join(DIR_PATH, sub_dir, filename)


def chk_with_org(filename, chk_str):
    """Get file contents from file with expected data"""
    org_name = get_path(filename, IN_DIR)
    chk_name = get_path(filename, OUT_DIR)
    try:
        with open(org_name, "r") as fd:
            expect_str = fd.read()
    except IOError:
        with open(chk_name, "w") as fd:
            fd.write(chk_str)
        return (False, f"Missing file, check {org_name}")
    if chk_str != expect_str:
        with open(chk_name, "w") as fd:
            fd.write(chk_str)
        return (False, f"Unexpected content {chk_name} != {org_name} (expected)")
    return (True, "")


class TestPlane(unittest.TestCase):
    """Unit tests for geom_3d.PlaneFromNormal"""

    def test_is_in_plane(self):
        """Test method geom_3d.PlaneFromNormal.is_in_plane(point)."""
        x = [1, 0, 0]
        y = [0, 1, 0]
        z = [0, 0, 1]
        test_matrix = {
            # normal, point, test_inputs, precisions, expected_results
            "simple_normal_z": (
                z,
                [1, 1, 1],
                [[1, 1, 1], z, [1, 0, 1], [1, 0, 0.99999], [1, 0, 0.99999]],
                [None, None, None, None, 5, 6],
                [True, True, True, False, True, False],
            ),
        }
        div3 = 1 / 3
        v0_d3 = [div3, div3, div3]
        # Test 1e-6, only one component
        v1_d3 = [div3 + 1.0e-6, div3, div3]
        # Test 1e-6, divided equally over all components
        d3 = div3 + 1.0e-6 / 3
        v2_d3 = [d3, d3, d3]
        # Test 1e-6, divided irregularly over all components
        v3_d3 = [div3 + 0.2e-6, div3 + 0.3e-6, div3 + 0.5e-6]
        test_matrix["normal_z"] = (
            [1, 1, 1],
            x,
            [
                x,
                y,
                z,
                v0_d3,
                v1_d3,
                v1_d3,
                v1_d3,
                v2_d3,
                v2_d3,
                v2_d3,
                v3_d3,
                v3_d3,
                v3_d3,
            ],
            [None, None, None, None, None, 6, 7, None, 6, 7, None, 6, 7],
            [
                True,
                True,
                True,
                True,
                False,
                True,
                False,
                False,
                True,
                False,
                False,
                True,
                False,
            ],
        )
        for test_name, (
            normal,
            point,
            inputs,
            precisions,
            expecteds,
        ) in test_matrix.items():
            plane = geom_3d.PlaneFromNormal(geomtypes.Vec(normal), geomtypes.Vec(point))
            for in_point, precision, expected in zip(inputs, precisions, expecteds):
                prec = f"1e-{precision}" if precision else "None"
                msg = f"{test_name} failed for {in_point} with precision {prec}"
                if precision is None:
                    self.assertEqual(
                        plane.is_in_plane(geomtypes.Vec(in_point)), expected, msg
                    )
                else:
                    with geomtypes.FloatHandler(precision):
                        self.assertEqual(
                            plane.is_in_plane(geomtypes.Vec(in_point)), expected, msg
                        )


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
            ],
            "diagonal_meet_at_edge_centre": [
                # Lines
                [
                    geom_3d.Line3D([1, 1, 1], [-1, 1, 1]),
                    geom_3d.Line3D([0, -1, -1], [0, 0, 0]),
                ],
                # Expected result
                geomtypes.Vec3([0, 1, 1]),
            ],
            "parallel edges": [
                # Lines
                [
                    geom_3d.Line3D([1, 1, 1], [0, 1, 1]),
                    geom_3d.Line3D([1, 1, -1], [-1, 1, -1]),
                ],
                # Expected result
                None,
            ],
            "crossed_edges": [
                # Lines
                [
                    geom_3d.Line3D([1, 1, 1], [0, 1, 1]),
                    geom_3d.Line3D([1, -1, -1], [1, -1, 1]),
                ],
                # Expected result
                None,
            ],
        }
        for test_name, (lines, expected_result) in test_matrix.items():
            result = lines[0].intersect(lines[1])
            if not result == expected_result:
                self.fail(
                    f"{result} != {expected_result} (expected) for {test_name}"
                )


class TestFace(unittest.TestCase):
    """Test Face class."""

    def test_ensure_domain(self):
        """Test the method geom_3d.Face.test_ensure_domain."""
        dummy_face = geom_3d.Face(
            [
                    geomtypes.Vec3([1, 0, 0]),
                    geomtypes.Vec3([0, 1, 0]),
                    geomtypes.Vec3([-1, 0, 0]),
            ],
        )
        two_pi = 2 * math.pi
        test_matrix = {
            "0 deg": (0, 0),
            "45 deg": (math.pi / 4, math.pi / 4),
            "90 deg": (math.pi / 2, math.pi / 2),
            "135 deg": (3 * math.pi / 4, 3 * math.pi / 4),
            "180 deg": (math.pi, math.pi),
            "225 deg": (5 * math.pi / 4, -3 * math.pi / 4),
            "270 deg": (3 * math.pi / 2, -math.pi / 2),
            "315 deg": (7 * math.pi / 4, -math.pi / 4),
        }
        for test_case, (angle_in, angle_exp) in test_matrix.items():
            with geomtypes.FloatHandler(8):
                for i in [0, -1, 1]:
                    angle_out = dummy_face.ensure_domain(angle_in + i * two_pi)
                    if geomtypes.FloatHandler.ne(angle_out, angle_exp):
                        self.fail(f"failure for {test_case} + {i}x360: {angle_out} != {angle_exp}")

    def test_face_shapes(self):
        """Test the some methods for the Face class.

        The following is tested:
            - gravity property
            - first_vec property
            - the face normal (method)
            - angles property
            - outline property (with tests sorted_edge_intersections and
                edge_intersections properties implicitely).
        """
        skip = None  # use this value to skip the test
        test_matrix = {
            "square": {
                #          ^ y
                #          |
                #         4|
                #        _-+-_
                #      _/  |  \_
                #    _/    |    \_
                # --+------+------+--> x
                # -4 \_    |    _/ 4
                #      \_  |  _/
                #        '-+-'
                #        -4|
                #          |
                "vs": [
                    geomtypes.Vec3([4, 0, 0]),
                    geomtypes.Vec3([0, 4, 0]),
                    geomtypes.Vec3([-4, 0, 0]),
                    geomtypes.Vec3([0, -4, 0]),
                ],
                "flip_normal": {},
                "expected": {
                    "gravity": geomtypes.Vec3([0, 0, 0]),
                    "first_vec": geomtypes.Vec3([1, 0, 0]),
                    "normal": geomtypes.Vec3([0, 0, 1]),
                    "angles_deg": [0, 90, 180, 270],
                    "outline": [
                        geomtypes.Vec3([4, 0, 0]),
                        geomtypes.Vec3([0, 4, 0]),
                        geomtypes.Vec3([-4, 0, 0]),
                        geomtypes.Vec3([0, -4, 0]),
                    ],
                },
            },
            "5-star": {  # a star with concave points between all vertices (using ints)
                #   z
                #   ^
                # 18|                       . 4
                #   |                      /|
                # 16|                    .' |
                #   |                   /   |
                # 14|                  /    |
                #   |                 /     |
                # 12|               .'      |
                #   |              /        |
                # 10|             /         |
                #   |            /          |
                #  8| 2 ._______/___________|______________. 1
                #   |    '_    /            |       ___---'
                #  6|      '-_'            _----''''
                #   |       / '-_   ___--'' |
                #  4|      /    _-.-        |
                #   |     /__--'   '-._     |
                #  2|   .='            '-_  |
                #   |   0                 '-| 3
                #   +-----------------------.-----------------> y
                #  0    2    4    6    8    10   11   12   14
                "vs": [
                    geomtypes.Vec3([1, 2, 2]),
                    geomtypes.Vec3([1, 14, 8]),
                    geomtypes.Vec3([1, 2, 8]),
                    geomtypes.Vec3([1, 10, 0]),
                    geomtypes.Vec3([1, 10, 18]),
                ],
                "flip_normal": {},
                "expected": {
                    "gravity": geomtypes.Vec3([1, 7.6, 7.2]),
                    "first_vec": geomtypes.Vec3([0, -5.6, -5.2]).normalise(),
                    "normal": geomtypes.Vec3([1, 0, 0]),
                    "angles_deg": skip,
                    "outline": [
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
            "bowtie": {
                # A bowtie: mixes concave points and no concave points
                #
                #   y
                #   ^
                #  2| v2 ----------- v3
                #   |     '-_    _'
                #  1|        -.-'
                #   | v0   _-' '-_ v1
                #  0|----.---------.---> x
                #       1    2    3
                "vs": [
                    geomtypes.Vec3([1, 0, 1]),
                    geomtypes.Vec3([3, 0, 1]),
                    geomtypes.Vec3([1, 2, 1]),
                    geomtypes.Vec3([3, 2, 1]),
                ],
                "flip_normal": {},
                "expected": {
                    "gravity": geomtypes.Vec3([2, 1, 1]),
                    "first_vec": geomtypes.Vec3([-1, -1, 0]).normalise(),
                    "normal": geomtypes.Vec3([0, 0, 1]),
                    "angles_deg": [0, 90, 270, 180],
                    "outline": [
                        geomtypes.Vec3([1, 0, 1]),
                        geomtypes.Vec3([3, 0, 1]),
                        geomtypes.Vec3([2, 1, 1]),
                        geomtypes.Vec3([3, 2, 1]),
                        geomtypes.Vec3([1, 2, 1]),
                        geomtypes.Vec3([2, 1, 1]),
                    ],
                },
            },
            "hole-or-no": {
                # a shape where some would expect a hole
                #
                #   z
                #   ^     v6
                # 6 |       .-------------g+ v5
                #   |      /           .-'
                # 4 |     -  v3.......1..... v2
                #   |     |    |  .-'      |
                # 2 |    -   v4|-'         |
                # 1 | v0 +-----------------+ v1
                #   +---.--.--.--.--.--.--.--> x
                #      1  2  3     5     7
                #
                "vs": [
                    geomtypes.Vec3([1, 2, 1]),
                    geomtypes.Vec3([7, 2, 1]),
                    geomtypes.Vec3([7, 2, 4]),
                    geomtypes.Vec3([3, 2, 4]),
                    geomtypes.Vec3([3, 2, 2]),
                    geomtypes.Vec3([7, 2, 6]),
                    geomtypes.Vec3([2, 2, 6]),
                ],
                "flip_normal": {},
                "expected": {
                    "gravity": geomtypes.Vec3([30 / 7, 2, 24 / 7]),
                    "first_vec": skip,
                    "normal": geomtypes.Vec3([0, -1, 0]),
                    "angles_deg": skip,
                    "outline": [
                        geomtypes.Vec3([1, 2, 1]),
                        geomtypes.Vec3([7, 2, 1]),
                        geomtypes.Vec3([7, 2, 4]),
                        geomtypes.Vec3([5, 2, 4]),
                        geomtypes.Vec3([7, 2, 6]),
                        geomtypes.Vec3([2, 2, 6]),
                    ],
                },
            },
            "crown": {
                # a shape where a vertex ends up in another edge
                #
                #   z
                #   ^
                # 3 |  |\_   _/|
                #   |  |  \ /  |
                # 1 |  +-------+
                #   +--.---.---.---> y
                #      1   3   5
                #
                "vs": [
                    geomtypes.Vec3([-1, 1, 1]),
                    geomtypes.Vec3([-1, 5, 1]),
                    geomtypes.Vec3([-1, 5, 3]),
                    geomtypes.Vec3([-1, 3, 1]),
                    geomtypes.Vec3([-1, 1, 3]),
                ],
                "flip_normal": {},
                "expected": {
                    "gravity": geomtypes.Vec3([-1, 3, 9 / 5]),
                    "first_vec": skip,
                    "normal": geomtypes.Vec3([1, 0, 0]),
                    "angles_deg": skip,
                    "outline": [
                        geomtypes.Vec3([-1, 1, 1]),
                        geomtypes.Vec3([-1, 3, 1]),
                        geomtypes.Vec3([-1, 5, 1]),
                        geomtypes.Vec3([-1, 5, 3]),
                        geomtypes.Vec3([-1, 3, 1]),
                        geomtypes.Vec3([-1, 1, 3]),
                    ],
                },
            },
            "double_intersection": {
                #   y
                #   ^
                #   |        3              6
                # 14|       _._            _.
                #   |     -'   -_       _-' |
                # 12|   .=_      '.   -'    |
                #   |  2   ''--_   '.'      |
                # 10|           '-'_ '._    |
                #   |          -'   ''-='-_ |
                #  8|        -'             |'+___
                #   |     _-'               |  ''--______
                #  6|   .'------------------+--------=._-'''====. 1
                #   |  0                    |           ''-__
                #  4|                       |                '_=. 4
                #   |                       |         __..--''
                #  2|                       |__..---''
                #   |                       5
                #   +-----------------------.----------------------> y
                #  0    2    4    6    8    10   11   12   13   14
                "vs": [
                    geomtypes.Vec3([2, 6, 0]),
                    geomtypes.Vec3([14, 6, 0]),
                    geomtypes.Vec3([2, 12, 0]),
                    geomtypes.Vec3([4, 14, 0]),
                    geomtypes.Vec3([14, 4, 0]),
                    geomtypes.Vec3([10, 2, 0]),
                    geomtypes.Vec3([10, 14, 0]),
                ],
                "flip_normal": {},
                "expected": {
                    "gravity": geomtypes.Vec3([8, 58 / 7, 0]),
                    "first_vec": skip,
                    "normal": geomtypes.Vec3([0, 0, 1]),
                    "angles_deg": skip,
                    "outline": [
                        geomtypes.Vec3([2, 6, 0]),
                        geomtypes.Vec3([10, 6, 0]),
                        geomtypes.Vec3([10, 2, 0]),
                        geomtypes.Vec3([14, 4, 0]),
                        geomtypes.Vec3([12, 6, 0]),
                        geomtypes.Vec3([14, 6, 0]),
                        geomtypes.Vec3([10, 8, 0]),
                        geomtypes.Vec3([10, 14, 0]),
                        geomtypes.Vec3([7, 11, 0]),
                        geomtypes.Vec3([4, 14, 0]),
                        geomtypes.Vec3([2, 12, 0]),
                        geomtypes.Vec3([6, 10, 0]),
                    ],
                },
            },
            "oops for noble stellation of RTC no. 6": {
                "vs": [
                    # integer version of that face:
                    #  19|               v7            v0
                    #    |               _+             +_
                    #  15|            .-' |             | '-_
                    #    |        v8 '-_  |             |  _-' v11
                    #  11| v3           '-|_           _|-'
                    #   9| _______________|_=_._____._=_|_______________ v4
                    #   7|  '-.           |    '-.-'    |           .-'
                    #    |     '-.        |   _-' '-_   |        .-'
                    #   3|        '-.     |.-'       '-.|     .-'
                    #   0|           '-.-'|             |'-_-'
                    #  -3|          .-' '-|             |_-'-.
                    #    |       .-'      |'-.        .-|     '-.
                    #  -7|    .-'         |   '-._ _-'  |        '-._
                    #  -9| _='____________|_____/__'____|____________-_ v9
                    # -11| v10            |.-'        '-|_
                    #    |            .-' |             | '-_
                    # -15|        v5 '-_  |             |  _-' v2
                    #    |              '-|             |-'
                    # -19|               v6            v1
                    #    +----------------------------------------------
                    #     -32    -16-14   -8  -4 0  4   8 14 16       32
                    geomtypes.Vec3([8, 19, 0]),  # v0
                    geomtypes.Vec3([8, -19, 0]),
                    geomtypes.Vec3([16, -15, 0]),
                    geomtypes.Vec3([-32, 9, 0]),  # v3
                    geomtypes.Vec3([32, 9, 0]),
                    geomtypes.Vec3([-16, -15, 0]),  # v5
                    geomtypes.Vec3([-8, -19, 0]),
                    geomtypes.Vec3([-8, 19, 0]),
                    geomtypes.Vec3([-16, 15, 0]),  # v8
                    geomtypes.Vec3([32, -9, 0]),
                    geomtypes.Vec3([-32, -9, 0]),  # 10
                    geomtypes.Vec3([16, 15, 0]),
                ],
                # Here: traversing from v0, v1, to v2 the normal will become (0, 0, -1)
                # Right turns, starting with vo will lead to one small triangle
                # However the reverse does lead to the whole outline, therefore the norma needs to
                # be flipped for the original only
                "flip_normal": {"reverse"},
                "expected": {
                    "gravity": skip,
                    "first_vec": skip,
                    "normal": skip,
                    "angles_deg": skip,
                    "outline": [
                        geom_3d.vec(8, 19, 0),
                        geom_3d.vec(8, 11, 0),
                        geom_3d.vec(16, 15, 0),
                    ],
                }
            },
            "similar to noble stellation of RTC no. 6": {
                "vs": [
                    # integer version of that face:
                    #  19|               v7            v0
                    #    |               _+             +_
                    #  15|            .-' |             | '-_
                    #    |        v8 '-_  |             |  _-' v11
                    #  11| v3           '-|_           _|-'
                    #   9| _______________|_=_._____._=_|_______________ v4
                    #   7|  '-.           |    '-.-'    |           .-'
                    #    |     '-.        |   _-' '-_   |        .-'
                    #   3|        '-.     |.-'       '-.|     .-'
                    #   0|           '-.-'|             |'-_-'
                    #  -3|          .-' '-|             |_-'-.
                    #    |       .-'      |'-.        .-|     '-.
                    #  -7|    .-'         |   '-.__--'  |        '-._
                    #  -9| _='____________|_____=__=____|____________-_ v9
                    # -11| v10            |.-'        '-|_
                    #    |            .-' |             | '-_
                    # -15|        v5 '-_  |             |  _-' v2
                    #    |              '-|             |-'
                    # -19|               v6            v1
                    #    +----------------------------------------------
                    #     -32    -16-14   -8  -4 0  4   8 14 16       32
                    geomtypes.Vec3([8, 19, 0]),  # v0
                    geomtypes.Vec3([8, -19, 0]),
                    geomtypes.Vec3([16, -15, 0]),
                    geomtypes.Vec3([-32, 9, 0]),  # v3
                    geomtypes.Vec3([32, 9, 0]),
                    geomtypes.Vec3([-16, -15, 0]),  # v5
                    geomtypes.Vec3([-8, -19, 0]),
                    geomtypes.Vec3([-8, 19, 0]),
                    geomtypes.Vec3([-16, 15, 0]),  # v8
                    geomtypes.Vec3([32, -9, 0]),
                    geomtypes.Vec3([-32, -9, 0]),  # 10
                    geomtypes.Vec3([16, 15, 0]),
                ],
                # Here: traversing from v0, v1, to v2 the normal will become (0, 0, -1)
                # Right turns, starting with vo will lead to one small triangle
                # However the reverse does lead to the whole outline, therefore the norma needs to
                # be flipped for the original only
                "flip_normal": {"org"},
                "expected": {
                    "gravity": skip,
                    "first_vec": skip,
                    "normal": skip,
                    "angles_deg": skip,
                    "outline": [
                        geom_3d.vec(8, 19, 0),
                        geom_3d.vec(8, 11, 0),
                        geom_3d.vec(4, 9, 0),
                        geom_3d.vec(-4, 9, 0),
                        geom_3d.vec(-8, 11, 0),
                        geom_3d.vec(-8, 19, 0),
                        geom_3d.vec(-16, 15, 0),
                        geom_3d.vec(-8, 11, 0),
                        geom_3d.vec(-8, 9, 0),
                        geom_3d.vec(-32, 9, 0),
                        geom_3d.vec(-14, 0, 0),
                        geom_3d.vec(-32, -9, 0),
                        geom_3d.vec(-8, -9, 0),
                        geom_3d.vec(-8, -11, 0),
                        geom_3d.vec(-16, -15, 0),
                        geom_3d.vec(-8, -19, 0),
                        geom_3d.vec(-8, -11, 0),
                        geom_3d.vec(-4, -9, 0),
                        geom_3d.vec(4, -9, 0),
                        geom_3d.vec(8, -11, 0),
                        geom_3d.vec(8, -19, 0),
                        geom_3d.vec(16, -15, 0),
                        geom_3d.vec(8, -11, 0),
                        geom_3d.vec(8, -9, 0),
                        geom_3d.vec(32, -9, 0),
                        geom_3d.vec(14, 0, 0),
                        geom_3d.vec(32, 9, 0),
                        geom_3d.vec(8, 9, 0),
                        geom_3d.vec(8, 11, 0),
                        geom_3d.vec(16, 15, 0),
                    ],
                }
            },
            "noble octagrammic icositetrahedron ": {
                "vs": [
                    # source: https://polytope.miraheze.org/wiki/Noble_octagrammic_icositetrahedron
                    #              v3
                    #                         v0
                    #                   .
                    #                                v5
                    #              .          .
                    #
                    #      v1                 .
                    #         .
                    #      v6                 .
                    #
                    #              .          .
                    #                                v2
                    #                   -
                    #                         v7
                    #              v4
                    geom_3d.vec(2.647899035704787,   4.113470267581556,  0.5),  # 0
                    geom_3d.vec(-2.647899035704787,  0.5,                4.113470267581556),  # 1
                    geom_3d.vec(4.113470267581556,  -2.647899035704787, -0.5),  # 2
                    geom_3d.vec(-0.5,                4.113470267581556,  2.647899035704787),  # 3
                    geom_3d.vec(-0.5,               -4.113470267581556,  2.647899035704787),  # 4
                    geom_3d.vec(4.113470267581556,   2.647899035704787, -0.5),  # 5
                    geom_3d.vec(-2.647899035704787, -0.5,                4.113470267581556),  # 6
                    geom_3d.vec(2.647899035704787,  -4.113470267581556,  0.5),  # 7
                ],
                "flip_normal": {},
                "expected": {
                    "gravity": skip,
                    "first_vec": skip,
                    "normal": skip,
                    "angles_deg": skip,
                    "outline": [
                        geom_3d.vec(2.6478990357048, 4.1134702675816, 0.5),
                        geom_3d.vec(0.5, 2.6478990357048, 1.9655712318768),
                        geom_3d.vec(-0.5, 4.1134702675816, 2.6478990357048),
                        geom_3d.vec(-0.5, 1.9655712318768, 2.6478990357048),
                        geom_3d.vec(-2.6478990357048, 0.5, 4.1134702675816),
                        geom_3d.vec(-1.5739495178524, 0, 3.3806846516432),
                        geom_3d.vec(-2.6478990357048, -0.5, 4.1134702675816),
                        geom_3d.vec(-0.5, -1.9655712318768, 2.6478990357048),
                        geom_3d.vec(-0.5, -4.1134702675816, 2.6478990357048),
                        geom_3d.vec(0.5, -2.6478990357048, 1.9655712318768),
                        geom_3d.vec(2.6478990357048, -4.1134702675816, 0.5),
                        geom_3d.vec(2.6478990357048, -1.9655712318768, 0.5),
                        geom_3d.vec(4.1134702675816, -2.6478990357048, -0.5),
                        geom_3d.vec(2.6478990357048, -0.5, 0.5),
                        geom_3d.vec(2.6478990357048, 0.5, 0.5),
                        geom_3d.vec(4.1134702675816, 2.6478990357048, -0.5),
                        geom_3d.vec(2.6478990357048, 1.9655712318768, 0.5),
                    ],
                },
            },
        }

        def my_reverse(lst):
            """convert [0, 1, .., n-2, n-1] to [0, n-1, n-2, .., 1].

            Handle skip value gracefully
            """
            return skip if lst is skip else lst[0:1] + lst[:0:-1]

        def new_angles(angles):
            """Convert angles for a reversed array."""
            return skip if angles is skip else [
                -a % 360 for a in my_reverse(angles)
            ]

        # Test for each their reverse:
        test_matrix = test_matrix | {
            name + "_reverse": {
                "vs": my_reverse(data["vs"]),
                "flip_normal": data["flip_normal"],
                "expected": {
                    "gravity": data["expected"]["gravity"],
                    "first_vec": data["expected"]["first_vec"],
                    "normal": -data["expected"]["normal"] if data["expected"]["normal"] else skip,
                    "angles_deg": new_angles(data["expected"]["angles_deg"]),
                    "outline": my_reverse(data["expected"]["outline"]),
                },
            }
            for name, data in test_matrix.items()
        }

        for test_case, test_data in test_matrix.items():
            vs = test_data["vs"]
            expected = test_data["expected"]
            test_face = geom_3d.Face(vs)

            if "reverse" in test_case:
                if "reverse" in test_data["flip_normal"]:
                    test_face.flip_normal()
            elif "org" in test_data["flip_normal"]:
                test_face.flip_normal()

            # Test gravity attribute
            if expected["gravity"] is not skip:
                self.assertEqual(
                    test_face.gravity,
                    expected["gravity"],
                    f"while testing gravity for {test_case}",
                )

            # Test first_vac attribute
            if expected["first_vec"] is not skip:
                self.assertEqual(
                    test_face.first_vec,
                    expected["first_vec"],
                    f"while testing first_vec for {test_case}",
                )

            # Test normal attribute
            if expected["normal"] is not skip:
                self.assertEqual(
                    test_face.normal_n,
                    expected["normal"],
                    f"while testing normal for {test_case}",
                )

            # Test angles attribute
            expected_angles = expected["angles_deg"]
            if expected_angles is not skip:
                if expected_angles:
                    result = test_face.angles
                    self.assertEqual(
                        len(result), len(expected_angles), f"while testing {test_case}"
                    )
                    for i, (expected_angle, angle) in enumerate(zip(expected_angles, result)):
                        if expected_angle is not skip:
                            self.assertEqual(
                                angle / geom_3d.DEG2RAD,
                                expected_angle,
                                f"while testing angles for {test_case}, angle #{i} (got {result})",
                            )

            # Test len, iter and outline attribute
            result = test_face.outline
            self.assertEqual(
                len(result),
                len(expected["outline"]),
                f"while testing amount of concave points for {test_case}, got {len(result)}",
            )
            errors = []
            with geomtypes.FloatHandler(12):
                for i, (expected_point, point) in enumerate(
                    zip(expected["outline"], result)
                ):
                    if point != expected_point:
                        errors.append(i)
            if errors:
                error_str = f"Unexpected result while testing concave points for {test_case}:\n"
                result_str = "["
                expected_str = "["
                for i, (expected_point, point) in enumerate(
                    zip(expected["outline"], result)
                ):
                    result_str += f"  {i}. {point}\n"
                    expected_str += f"  {i}. {expected_point}\n"
                result_str += "]"
                expected_str += "]"
                error_str += f"{result_str} !=\n{expected_str} (expected)\n for {errors}"
                self.fail(error_str)


class TestSimpleShape(unittest.TestCase):
    """Unit tests for geom_3d.SimpleShape that aren't inherited"""
    def test_proper_edges(self):
        """Test the method check_proper_edges."""
        test_matrix = {
            "tetrahedron": {
                "shape": get_tetrahedron(),
                "test_pars": [
                    {"restrict": True, "expect": True},
                    {"restrict": False, "expect": True},
                ]
            },
            "tetrahedron_min_one": {
                "vs": [
                    geomtypes.Vec3([1, 1, 1]),
                    geomtypes.Vec3([-1, -1, 1]),
                    geomtypes.Vec3([1, -1, -1]),
                    geomtypes.Vec3([-1, 1, -1]),
                ],
                "fs": [
                    [0, 1, 2],
                    [0, 3, 1],
                    [2, 3, 0],
                ],
                "test_pars": [
                    {"restrict": True, "expect": False},
                    {"restrict": False, "expect": False},
                ]
            },
            "shared edges 4 times": {
                "vs": [
                    geomtypes.Vec3([1, 1, 1]),
                    geomtypes.Vec3([-1, -1, 1]),
                    geomtypes.Vec3([1, -1, -1]),
                ],
                "fs": [
                    [0, 1, 2],
                    [0, 1, 2],
                    [0, 1, 2],
                    [0, 1, 2],
                ],
                "test_pars": [
                    {"restrict": True, "expect": False},
                    {"restrict": False, "expect": True},
                ]
            },
            "shared edges 4 times split": {
                "vs": [
                    geomtypes.Vec3([1, 1, 1]),
                    geomtypes.Vec3([-1, -1, 1]),
                    geomtypes.Vec3([1, -1, -1]),
                    geomtypes.Vec3([1, 1, 1]),
                    geomtypes.Vec3([-1, -1, 1]),
                    geomtypes.Vec3([1, -1, -1]),
                ],
                "fs": [
                    [0, 1, 2],
                    [0, 1, 2],
                    [3, 4, 5],
                    [3, 4, 5],
                ],
                "test_pars": [
                    {"restrict": True, "expect": True},
                    {"restrict": False, "expect": True},
                ]
            },
        # TODO: test with clean up shape?
        }
        for test_case, data in test_matrix.items():
            if data.get("shape"):
                shape = data["shape"]
            else:
                shape = geom_3d.SimpleShape(vs=data["vs"], fs=data["fs"], colors=([YELLOW], []))
            for result in data["test_pars"]:
                self.assertEqual(
                    shape.check_proper_edges(restrict=result["restrict"]),
                    result["expect"],
                    f"test case '{test_case}' failed for check_proper_edges.",
                )


class TestSimpleShapeInherit(unittest.TestCase):
    """Unit tests for geom_3d.SimpleShape"""

    shape = None
    name = "simple_shape"
    ps_margin = 10
    ps_precision = 7
    off_precision = 15
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
        tst_str = self.shape.to_off(precision=self.off_precision)
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


class TestSimpleShapeExtended(TestSimpleShapeInherit):
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
            vs=[
                geomtypes.Vec3([1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, -1.0, -1.0]),
                geomtypes.Vec3([1.0, -1.0, -1.0]),
            ],
            fs=[
                [0, 1, 2, 3],
                [0, 3, 7, 4],
                [1, 0, 4, 5],
                [2, 1, 5, 6],
                [3, 2, 6, 7],
                [7, 6, 5, 4],
            ],
            es=[0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6, 2, 6, 6, 7],
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
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([-0.5, 0.5, -0.5, -0.5]),
                        geomtypes.Quat([-0.5, -0.5, 0.5, 0.5]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([-v2_div_2, 0, -v2_div_2, 0]),
                        geomtypes.Quat([-v2_div_2, 0, v2_div_2, 0]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([0, 0, -v2_div_2, -v2_div_2]),
                        geomtypes.Quat([0, 0, v2_div_2, v2_div_2]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([v2_div_2, -v2_div_2, 0, 0]),
                        geomtypes.Quat([v2_div_2, v2_div_2, 0, 0]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([0, -v2_div_2, v2_div_2, 0]),
                        geomtypes.Quat([0, v2_div_2, -v2_div_2, 0]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([0.5, -0.5, -0.5, -0.5]),
                        geomtypes.Quat([0.5, 0.5, 0.5, 0.5]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([-0.5, -0.5, 0.5, -0.5]),
                        geomtypes.Quat([-0.5, 0.5, -0.5, 0.5]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([0, v2_div_2, 0, -v2_div_2]),
                        geomtypes.Quat([0, -v2_div_2, 0, v2_div_2]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([-v2_div_2, -v2_div_2, 0, 0]),
                        geomtypes.Quat([-v2_div_2, v2_div_2, 0, 0]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([0, v2_div_2, 0, v2_div_2]),
                        geomtypes.Quat([0, -v2_div_2, 0, -v2_div_2]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([0, 0, -v2_div_2, v2_div_2]),
                        geomtypes.Quat([0, 0, v2_div_2, -v2_div_2]),
                    )
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([v2_div_2, 0, -v2_div_2, 0]),
                        geomtypes.Quat([v2_div_2, 0, v2_div_2, 0]),
                    )
                ),
            ],
            name=self.name,
            orientation=geomtypes.Rot3(
                (
                    geomtypes.Quat(
                        [0.953020613871, 0.214186495298, 0.0, 0.214186495298]
                    ),
                    geomtypes.Quat(
                        [0.953020613871, -0.214186495298, 0.0, -0.214186495298]
                    ),
                )
            ),
        )
        # for debugging:
        # self.shape.json_indent = 2


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
            vs=[
                geomtypes.Vec3([1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, -1.0, -1.0]),
                geomtypes.Vec3([1.0, -1.0, -1.0]),
            ],
            fs=[
                [0, 1, 2, 3],
                [0, 3, 7, 4],
                [1, 0, 4, 5],
                [2, 1, 5, 6],
                [3, 2, 6, 7],
                [7, 6, 5, 4],
            ],
            es=[0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6, 2, 6, 6, 7],
            colors=[
                [0.996094, 0.839844, 0.0],
                [0.132812, 0.542969, 0.132812],
                [0.542969, 0.0, 0.0],
                [0.0, 0.746094, 0.996094],
                [0.542969, 0.523438, 0.304688],
            ],
            isometries=[
                geomtypes.Rot3(
                    (geomtypes.Quat([-a, -0.5, b, 0]), geomtypes.Quat([-a, 0.5, -b, 0]))
                ),
                geomtypes.Rot3(
                    (geomtypes.Quat([a, -b, 0, -0.5]), geomtypes.Quat([a, b, 0, 0.5]))
                ),
                geomtypes.Rot3(
                    (
                        geomtypes.Quat([0.5, 0.5, -0.5, -0.5]),
                        geomtypes.Quat([0.5, -0.5, 0.5, 0.5]),
                    )
                ),
                geomtypes.Rot3(
                    (geomtypes.Quat([0.5, 0, -b, a]), geomtypes.Quat([0.5, 0, b, -a]))
                ),
                geomtypes.Rot3(
                    (geomtypes.Quat([0, -0.5, a, b]), geomtypes.Quat([0, 0.5, -a, -b]))
                ),
            ],
            name=self.name,
            orientation=geomtypes.Rot3(
                (
                    geomtypes.Quat([1.0, 0.0, 0.0, 0.0]),
                    geomtypes.Quat([1.0, 0.0, 0.0, 0.0]),
                )
            ),
        )
        # for debugging:
        # self.shape.json_indent = 2


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
            vs=[
                geomtypes.Vec3([1.0, -0.5, 1.0]),
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
                geomtypes.RotInv3(
                    angle=2 * math.pi / 3, axis=geomtypes.Vec3([-1, 1, 1])
                ),
            ],
            name=self.name,
            # orientation=geomtypes.Rot3(angle=math.pi/4, axis=geomtypes.Vec3([0, 0, 1]))
        )
        # for debugging:
        # self.shape.json_indent = 2


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
        self.shape.orientation = geomtypes.Rot3(
            angle=math.pi / 4, axis=geomtypes.Vec3([0, 0, 1])
        )
        self.shape.name = self.name
        # for debugging:
        # self.shape.json_indent = 2


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
            vs=[
                geomtypes.Vec3([1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, 1.0, 1.0]),
                geomtypes.Vec3([-1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, -1.0, 1.0]),
                geomtypes.Vec3([1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, 1.0, -1.0]),
                geomtypes.Vec3([-1.0, -1.0, -1.0]),
                geomtypes.Vec3([1.0, -1.0, -1.0]),
            ],
            fs=[
                [0, 1, 2, 3],
                [0, 3, 7, 4],
                [1, 0, 4, 5],
                [2, 1, 5, 6],
                [3, 2, 6, 7],
                [7, 6, 5, 4],
            ],
            es=[0, 1, 1, 2, 2, 3, 0, 3, 3, 7, 4, 7, 0, 4, 4, 5, 1, 5, 5, 6, 2, 6, 6, 7],
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
        # self.shape.json_indent = 2


class TestTetraCompound(TestSimpleShapeExtended):
    """Unit tests for orbit.Shape and fix for issue 24.

    Note: this test uses the module orbit and not geom_3d, but indirectly geom_3d is tested.
    This test was introduced to test the fix for issue 24 lead to missing lines in PostScript files
    due to orthogonal planes. The fix was needed in geom_3d and that is why this test is part of
    this file and at the time of writing there was not unit test for the orbit scene (besides
    perhaps the shape should be moved).
    """
    off_precision = 14
    ps_margin = 6
    name = "tet_4_D4xI_D2C2"
    scale = 200

    def def_shape(self):
        """Define shape"""
        tetrahedron = get_tetrahedron()
        rot_45deg_x = geomtypes.Rot3(axis=geomtypes.Vec3([1, 0, 0]), angle=math.pi / 4)
        tetrahedron.transform(rot_45deg_x)
        self.shape = orbit.Shape(
            {
                "vs": tetrahedron.vs,
                "fs": tetrahedron.fs,
            },
            isometry.D4xI(
                setup={
                    "axis_n": geomtypes.Vec([0, 0, 1]),
                    "axis_2": geomtypes.Vec([1, 0, 0]),
                }
            ),
            isometry.D2C2(
                setup={
                    "axis_n": geomtypes.Vec([1, 0, 0]),
                    "normal_r": geomtypes.Vec([0, 1, 0]),
                }
            ),
            self.name,
            no_of_cols=2,
            cols=[rgb.plum, rgb.gold],
        )
        # for debugging:
        # self.shape.json_indent = 2


if __name__ == "__main__":
    unittest.main()
