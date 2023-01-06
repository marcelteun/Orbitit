#!/usr/bin/env python
"""Test module for orbitit.geom_2d.py"""
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
#
# ------------------------------------------------------------------
import unittest

from orbitit import geom_2d, geomtypes

class TestLine(unittest.TestCase):
    """Unit tests for geom_2d.Line"""

    def test_intersect_2d_line_with_other_line(self):
        """Test intersect and thus intersect_get_factor"""
        test_matrix = {  # test_case: (p0, v0, p1, p2, expected point)
            "line 0": (
                geomtypes.Vec([1, 2]),
                geomtypes.Vec([1, 1]),
                geomtypes.Vec([1, 0.3]),
                geomtypes.Vec([2, 3]),
                geomtypes.Vec([2, 3]),
            ),
        }
        for case, (p, v, p0, p1, expect) in test_matrix.items():
            l0 = geom_2d.Line(p, v=v)
            l1 = geom_2d.Line(p0, p1=p1)
            result = l0.intersect(l1)
            self.assertTrue(
                result == expect,
                f"Error for '{case}': {result} != {expect} (expected)"
            )
        precision = 5
        # check precision ok
        margin_ok = 0.9 * 10**-precision
        for case, (p, v, p0, p1, expect) in test_matrix.items():
            l0 = geom_2d.Line(p, v=v)
            d = margin_ok
            l1 = geom_2d.Line(p0, p1=geomtypes.Vec([p1[0] + d, p1[1] + d]))
            result = l0.intersect(l1)
            with geomtypes.FloatHandler(precision):
                self.assertTrue(
                    result == expect,
                    f"Error for '{case}': {result} != {expect} (expected)"
                )
        margin_nok = 1.1 * 10**-precision
        for case, (p, v, p0, p1, expect) in test_matrix.items():
            l0 = geom_2d.Line(p, v=v)
            d = margin_nok
            l1 = geom_2d.Line(p0, p1=geomtypes.Vec([p1[0] + d, p1[1] + d]))
            result = l0.intersect(l1)
            with geomtypes.FloatHandler(precision):
                self.assertFalse(
                    result == expect,
                    f"Error for '{case}': delta |{result - expect}| < 1*10^-{precision}"
                )

    def test_2d_line_left_or_right_side(self):
        """Test function that states on what side a point is."""
        test_matrix = {  # test case: line, point, expected result
            "orig, orig": (geom_2d.Line([0, 0], [1, 1]), [0, 0], 0),
            "through orig, orig": (geom_2d.Line([-1, -1], [1, 1]), [0, 0], 0),
            "orig 45, left 1": (geom_2d.Line([-1, -1], [1, 1]), [0, 1], -1),
            "orig 45, right 1": (geom_2d.Line([-1, -1], [1, 1]), [0, -1], 1),
            "orig hor, on 1": (geom_2d.Line([0, 0], v=[1, 0]), [4, 0], 0),
            "orig hor, left 1": (geom_2d.Line([0, 0], v=[1, 0]), [1, 2], -1),
            "orig hor, left 2": (geom_2d.Line([0, 0], v=[-1, 0]), [-1, -2], -1),
            "orig hor, right 1": (geom_2d.Line([0, 0], v=[1, 0]), [-1, -2], 1),
            "orig hor, right 2": (geom_2d.Line([0, 0], v=[-1, 0]), [1, 2], 1),
            "orig vert, on 1": (geom_2d.Line([0, 0], v=[0, 1]), [0, -2], 0),
            "orig vert, left 1": (geom_2d.Line([0, 0], v=[0, 1]), [-3, 1], -1),
            "orig vert, left 2": (geom_2d.Line([0, 0], v=[0, -1]), [3, -1], -1),
            "orig vert, right 1": (geom_2d.Line([0, 0], v=[0, 1]), [3, -1], 1),
            "orig vert, right 2": (geom_2d.Line([0, 0], v=[0, -1]), [-3, 1], 1),
            "gen, on 1": (geom_2d.Line([-1, 1], v=[2, 1]), [3, 3], 0),
            "gen, left 1": (geom_2d.Line([-1, 1], v=[2, 1]), [3, 5], -1),
            "gen, left 2": (geom_2d.Line([-1, 1], v=[-2, -1]), [3, 0], -1),
            "gen, right 1": (geom_2d.Line([-1, 1], v=[2, 1]), [3, 0], 1),
            "gen, right 2": (geom_2d.Line([-1, 1], v=[-2, -1]), [3, 5], 1),
        }
        for test_case, (line, point, expected) in test_matrix.items():
            self.assertEqual(  # False positive below for pyline 2.4.4
                line.at_side_of(point),  # pylint: disable=no-member
                expected,
                f"Test case {test_case} failed"
            )

class TestPolygon(unittest.TestCase):
    """Unit tests for geom_2d.Polygon"""

    def test_slice(self):
        """Test slice method."""
        test_matrix = {  # test case: coords, vs, slice, expected result
            "index 0": ([[0, 0], [1, 1], [2, 2]], [0, 1, 2], 0, [0, 0]),
            "index -1": ([[0, 0], [1, 1], [2, 2]], [0, 1, 2], -1, [2, 2]),
            "index high": ([[0, 0], [1, 1], [2, 2]], [0, 1, 2], 4, [1, 1]),
            "start, stop inside": (
                [[0, 0], [1, 1], [2, 2]], [0, 1, 2], slice(0, 2, None), [[0, 0], [1, 1]]
            ),
            "start, stop wrap once": (
                [[0, 0], [1, 1], [2, 2]], [0, 1, 2], slice(-1, 1, None), [[2, 2], [0, 0]]
            ),
            "start, stop high wrap once": (
                [[0, 0], [1, 1], [2, 2]], [0, 1, 2], slice(5, 7, None), [[2, 2], [0, 0]]
            ),
            "start, stop wrap multi": (
                [[0, 0], [1, 1], [2, 2]], [0, 1, 2], slice(-1, 4, None), [[2, 2], [0, 0]]
            ),
            "start, stop, step inside": (
                [[0, 0], [1, 1], [2, 2]], [0, 1, 2], slice(0, 3, 2), [[0, 0], [2, 2]]
            ),
            "start, stop, step wrap just": (
                [[0, 0], [1, 1], [2, 2]], [0, 1, 2], slice(0, 3, 2), [[0, 0], [2, 2]]
            ),
            "start, stop, step wrap once": (
                [[0, 0], [1, 1], [2, 2]], [0, 1, 2], slice(-1, 2, 2), [[2, 2], [1, 1]]
            ),
            # for now this doesn't work, #TODO implement opposite direction
            "start, stop high opposite": (
                [[0, 0], [1, 1], [2, 2]], [0, 1, 2], slice(5, 4, None), []
            ),
        }
        for test_case, (c, vs, idx, expected) in test_matrix.items():
            p = geom_2d.Polygon(c, vs)
            v = p[idx]
            self.assertEqual(v, expected, f"Test case {test_case} failed")


if __name__ == '__main__':
    unittest.main()
