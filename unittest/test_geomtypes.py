#!/usr/bin/env python
"""Test geomtypes."""
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
import os
import random
import unittest

from orbitit import geomtypes


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class Rounding(unittest.TestCase):
    """Test rounding of floats"""

    def test_float_handler(self):
        """Test some basic stuff"""
        a = 0.12345678
        b = 0.12345673

        self.assertFalse(a == b)
        self.assertEqual(geomtypes.FloatHandler.to_str(a), "0.12345678")
        self.assertEqual(geomtypes.FloatHandler.to_str(b), "0.12345673")

        with geomtypes.FloatHandler(8) as fh:
            self.assertFalse(fh.eq(a, b))
            str_a = fh.to_str(a)
            str_b = fh.to_str(b)
        self.assertEqual(str_a, "0.12345678")
        self.assertEqual(str_b, "0.12345673")

        with geomtypes.FloatHandler(7):
            self.assertTrue(fh.eq(a, b))
            str_a = fh.to_str(a)
            str_b = fh.to_str(b)
        self.assertEqual(str_a, "0.1234568")
        self.assertEqual(str_b, "0.1234567")

    def test_rounded_float(self):
        """Test comparison of RoundedFloat with different margins."""
        a = geomtypes.RoundedFloat(0.12345678)
        b = geomtypes.RoundedFloat(0.12345673)

        self.assertFalse(a == b)
        self.assertEqual(str(a), "0.12345678")
        self.assertEqual(repr(a), "0.12345678")
        self.assertEqual(str(b), "0.12345673")
        self.assertEqual(repr(b), "0.12345673")

        with geomtypes.FloatHandler(8):
            self.assertFalse(a == b)
            self.assertEqual(str(a), "0.12345678")
            self.assertEqual(repr(a), "0.12345678")
            self.assertEqual(str(b), "0.12345673")
            self.assertEqual(repr(b), "0.12345673")

        with geomtypes.FloatHandler(7):
            self.assertTrue(a == b)
            self.assertEqual(str(a), "0.1234568")
            self.assertEqual(repr(a), "0.1234568")
            self.assertEqual(str(b), "0.1234567")
            self.assertEqual(repr(b), "0.1234567")

    def test_all_cmp(self):
        """Test all comparison functions."""
        a = geomtypes.RoundedFloat(0.12345678)
        b = geomtypes.RoundedFloat(0.12345673)

        self.assertFalse(a == b)
        self.assertFalse(a <= b)
        self.assertFalse(a < b)
        self.assertTrue(a >= b)
        self.assertTrue(a > b)
        self.assertTrue(a != b)

        with geomtypes.FloatHandler(7):
            self.assertFalse(a != b)
            self.assertFalse(a < b)
            self.assertFalse(a > b)
            self.assertTrue(a <= b)
            self.assertTrue(a >= b)
            self.assertTrue(a == b)
            self.assertFalse(b != a)
            self.assertFalse(b < a)
            self.assertFalse(b > a)
            self.assertTrue(b <= a)
            self.assertTrue(b >= a)
            self.assertTrue(b == a)

    def test_keep_type(self):
        """Test whether operations on RoundedFloat return RoundedFloat."""
        a = geomtypes.RoundedFloat(1.)
        b = geomtypes.RoundedFloat(2.)

        result = -a
        self.assertTrue(isinstance(result, geomtypes.RoundedFloat))
        self.assertEqual(result, -1)

        result = +a
        self.assertTrue(isinstance(result, geomtypes.RoundedFloat))
        self.assertEqual(result, a)

        result = b ** 4
        self.assertTrue(isinstance(result, geomtypes.RoundedFloat))
        self.assertEqual(result, 16)

        def chk(a, b):
            """Test binary operators where __r<op>__ exists."""
            result = a + b
            self.assertTrue(isinstance(result, geomtypes.RoundedFloat))
            self.assertEqual(result, 3)

            result = a - b
            self.assertTrue(isinstance(result, geomtypes.RoundedFloat))
            self.assertEqual(result, -1)

            result = a * b
            self.assertTrue(isinstance(result, geomtypes.RoundedFloat))
            self.assertEqual(result, 2)

            result = a / b
            self.assertTrue(isinstance(result, geomtypes.RoundedFloat))
            self.assertEqual(result, 0.5)

        chk(a, b)
        chk(float(a), b)
        chk(a, float(b))

    def test_mix(self):
        """Test mixing RoundedFloat and float."""
        a = geomtypes.RoundedFloat(0.12345678)
        b = 0.12345673

        self.assertFalse(a == b)
        self.assertFalse(a <= b)
        self.assertFalse(a < b)
        self.assertTrue(a >= b)
        self.assertTrue(a > b)
        self.assertTrue(a != b)

        with geomtypes.FloatHandler(7):
            self.assertFalse(a != b)
            self.assertFalse(a < b)
            self.assertFalse(a > b)
            self.assertTrue(a <= b)
            self.assertTrue(a >= b)
            self.assertTrue(a == b)
            self.assertFalse(b != a)
            self.assertFalse(b < a)
            self.assertFalse(b > a)
            self.assertTrue(b <= a)
            self.assertTrue(b >= a)
            self.assertTrue(b == a)


class TestVec(unittest.TestCase):
    """Unit tests for geomtypes.Vec and derivatives"""

    def test_basic(self):
        """Some basic tests: init, add, sub, mul, div"""
        r = geomtypes.Vec([])
        self.assertEqual(r, [])

        v = geomtypes.Vec([1, 2, 4])
        w = geomtypes.Vec([2, 3, 5, 6])

        r = -v
        self.assertEqual(r, geomtypes.Vec([-1.0, -2.0, -4.0]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

        r = v+w
        self.assertEqual(r, geomtypes.Vec([3.0, 5.0, 9.0]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

        r = w-v
        self.assertEqual(r, geomtypes.Vec([1.0, 1.0, 1.0]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

        r = v*2
        self.assertEqual(r, geomtypes.Vec([2.0, 4.0, 8.0]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

        r = 2*v
        self.assertEqual(r, geomtypes.Vec([2.0, 4.0, 8.0]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

        r = v/2
        self.assertEqual(r, geomtypes.Vec([0.5, 1.0, 2.0]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

        v = geomtypes.Vec([1.0, 5.0, 4.0])
        r = v[1:]
        self.assertEqual(r, geomtypes.Vec([5.0, 4.0]))

    def test_norm(self):
        """Some tests considering normalising vectors"""
        v = geomtypes.Vec([1, 2, 4])
        r = v.norm()
        self.assertEqual(r, math.sqrt(1+4+16))

        v = geomtypes.Vec([3, 4, 5])
        n = v.norm()
        r = v.normalize()
        self.assertEqual(r, geomtypes.Vec([v[0]/n, v[1]/n, v[2]/n]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

        r = v.normalise()
        self.assertEqual(r, geomtypes.Vec([v[0]/n, v[1]/n, v[2]/n]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

    def test_angle(self):
        """Test angle between vectors"""
        v = geomtypes.Vec([0, 0, 0])
        w = geomtypes.Vec([10, 0, 0])
        with self.assertRaises(ValueError):
            r = v.angle(w)

        v = geomtypes.Vec([10, 0, 0])
        w = geomtypes.Vec([0, 0, 0])
        with self.assertRaises(ValueError):
            r = v.angle(w)

        v = geomtypes.Vec([0, 0, 0])
        w = geomtypes.Vec([0, 0, 0])
        with self.assertRaises(ValueError):
            r = v.angle(w)

        v = geomtypes.Vec([4, 0, 0])
        w = geomtypes.Vec([10, 0, 0])
        r = v.angle(w)
        self.assertEqual(r, 0)

        v = geomtypes.Vec([10, 0, 0])
        w = geomtypes.Vec([0, 3, 0])
        r = v.angle(w)
        self.assertEqual(r, geomtypes.QUARTER_TURN)

        v = geomtypes.Vec([0, 10, 0])
        w = geomtypes.Vec([0, 3, 3])
        r = v.angle(w)
        self.assertEqual(r, math.pi/4)

        v = geomtypes.Vec([0, 10, 0])
        w = geomtypes.Vec([0, -3, 0])
        r = v.angle(w)
        self.assertEqual(r, geomtypes.HALF_TURN)

    def test_cross(self):
        """Test cross procuct"""
        v = geomtypes.Vec3([1, 2, 3])
        w = geomtypes.Vec3([2, -3, 4])
        r = v.cross(w)
        self.assertEqual(r, geomtypes.Vec3([17, 2, -7]))
        self.assertTrue(isinstance(r, geomtypes.Vec3))

        v = geomtypes.Vec3([1, 0, 0])
        w = geomtypes.Vec3([1, 0, 0])
        r = v.cross(w)
        self.assertEqual(r, geomtypes.Vec3([0, 0, 0]))
        self.assertTrue(isinstance(r, geomtypes.Vec3))

        v = geomtypes.Vec3([0, 0, 0])
        w = geomtypes.Vec3([1, 0, 0])
        r = v.cross(w)
        self.assertEqual(r, geomtypes.Vec3([0, 0, 0]))
        self.assertTrue(isinstance(r, geomtypes.Vec3))

        v = geomtypes.Vec3([1, 0, 0])
        w = geomtypes.Vec3([0, 0, 0])
        r = v.cross(w)
        self.assertEqual(r, geomtypes.Vec3([0, 0, 0]))
        self.assertTrue(isinstance(r, geomtypes.Vec3))

        v = geomtypes.Vec3([0, 0, 0])
        w = geomtypes.Vec3([0, 0, 0])
        r = v.cross(w)
        self.assertEqual(r, geomtypes.Vec3([0, 0, 0]))
        self.assertTrue(isinstance(r, geomtypes.Vec3))

    def test_quat_basic(self):
        """Test some basic functions"""
        q0 = geomtypes.Quat([1, 2, 3, 5])
        exp = geomtypes.Quat([2, 4, 6, 10])
        chk = q0 * 2
        self.assertEqual(chk, exp)
        chk = q0 * 2.0
        self.assertEqual(chk, exp)

        q0 = geomtypes.Quat([1, 2, 3, 5])
        q1 = geomtypes.Quat([2, 4, 3, 5])
        r = q0 * q1
        self.assertEqual(r, geomtypes.Quat([-40, 8, 19, 9]))
        self.assertTrue(isinstance(r, geomtypes.Quat))

        q0 = geomtypes.Quat([0, 0, 0, 0])
        q1 = geomtypes.Quat([2, 4, 3, 5])
        r = q0 * q1
        self.assertEqual(r, geomtypes.Quat([0, 0, 0, 0]))
        self.assertTrue(isinstance(r, geomtypes.Quat))

        q0 = geomtypes.Quat([1, 0, 0, 0])
        q1 = geomtypes.Quat([2, 4, 3, 5])
        r = q0 * q1
        self.assertEqual(r, geomtypes.Quat([2, 4, 3, 5]))
        self.assertTrue(isinstance(r, geomtypes.Quat))

        q0 = geomtypes.Quat([0, 1, 0, 0])
        q1 = geomtypes.Quat([2, 4, 3, 5])
        r = q0 * q1
        self.assertEqual(r, geomtypes.Quat([-4, 2, -5, 3]))
        self.assertTrue(isinstance(r, geomtypes.Quat))

        q0 = geomtypes.Quat([0, 0, 1, 0])
        q1 = geomtypes.Quat([2, 4, 3, 5])
        r = q0 * q1
        self.assertEqual(r, geomtypes.Quat([-3, 5, 2, -4]))
        self.assertTrue(isinstance(r, geomtypes.Quat))

        q0 = geomtypes.Quat([0, 0, 0, 1])
        q1 = geomtypes.Quat([2, 4, 3, 5])
        r = q0 * q1
        self.assertEqual(r, geomtypes.Quat([-5, -3, 4, 2]))
        self.assertTrue(isinstance(r, geomtypes.Quat))

        q = geomtypes.Quat([2, 4, 3, 5])
        r = q.S()
        self.assertEqual(r, 2)
        self.assertTrue(isinstance(r, float))
        r = q.V()
        self.assertEqual(r, geomtypes.Vec3([4, 3, 5]))
        self.assertTrue(isinstance(r, geomtypes.Vec))

        q = geomtypes.Quat([2, 4, 3, 5])
        r = q.conjugate()
        self.assertEqual(r, geomtypes.Quat([2, -4, -3, -5]))
        self.assertTrue(isinstance(r, geomtypes.Quat))

        q = geomtypes.Quat([2, 0, 0, 5])
        r = q.conjugate()
        self.assertEqual(r, geomtypes.Quat([2, 0, 0, -5]))
        self.assertTrue(isinstance(r, geomtypes.Quat))

        q = geomtypes.Quat([0, 0, 0, 0])
        r = q.conjugate()
        self.assertEqual(r, q)
        self.assertTrue(isinstance(r, geomtypes.Quat))

    def test_json(self):
        """Test saving to and loading from JSON."""
        test_matrix = [
            # test_vector, type
            ([], geomtypes.Vec),
            ([1], geomtypes.Vec),
            ([1, 2], geomtypes.Vec),
            ([1, 2, 3], geomtypes.Vec),
            ([-1.1, 1.2, math.pi], geomtypes.Vec),
            ([1, 2, 3], geomtypes.Vec3),
            ([0, 0, 0], geomtypes.Vec3),
            ([-1, 1, -2], geomtypes.Vec3),
            ([-1.1, 1.2, math.pi], geomtypes.Vec3),
            ([0, -1.1, 1.2, math.pi], geomtypes.Vec4),
            ([0, 0, 0, 0], geomtypes.Quat),
            ([1, 0, 0, 0], geomtypes.Quat),
            ([0, 0, 0, 1], geomtypes.Quat),
            ([1, 1, 1, 1], geomtypes.Quat),
            ([4/7, -1/2, 1/3, -math.sqrt(3)], geomtypes.Quat),
        ]
        # NOTE that for floats assertEqual will use the Vec.__eq__,
        # Which uses the geomtypes.FloatHandler
        # When saving floats in JSON, geomtypes.RoundedFloat is used,
        # which uses the same geomtypes.FloatHandler (Singleton)
        filename = os.path.join(DIR_PATH, "output", "test_vec.json")
        for v, cls in test_matrix:
            cls(v).write_json_file(filename)
            w = cls.from_json_file(filename)
            self.assertEqual(v, w)
            self.assertEqual(w, v)


class TestRot3(unittest.TestCase):
    """Unit tests for geomtypes.Rot3"""

    def test_basic(self):
        """Some basic tests of geomtypes.Rot3"""
        r = geomtypes.I * geomtypes.I
        self.assertNotEqual(geomtypes.I, geomtypes.E)
        self.assertEqual(r, geomtypes.E)

        q0 = geomtypes.Rot3(axis=geomtypes.UZ, angle=0)
        q1 = geomtypes.Rot3(axis=geomtypes.UZ, angle=2*math.pi)
        self.assertEqual(q0, q1)

        q0 = geomtypes.Rot3(axis=geomtypes.UZ, angle=math.pi)
        q1 = geomtypes.Rot3(axis=geomtypes.UZ, angle=-math.pi)
        self.assertEqual(q0, q1)

        r = geomtypes.Rot3(axis=geomtypes.Vec3([0, 0, 0]), angle=0)
        self.assertEqual(r[1], geomtypes.Quat([1, 0, 0, 0]))
        self.assertEqual(r[0], geomtypes.Quat([1, 0, 0, 0]))

    def test_rotation_around_z(self):
        """Test rotation around z-axis"""
        # rotation around z -axis
        # 0 degrees (+/- 360)
        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=0)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, geomtypes.UX)

        # same as above but specifying the axis as a list
        q = geomtypes.Rot3(axis=[0, 0, 1], angle=0)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, geomtypes.UX)

        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=geomtypes.FULL_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, geomtypes.UX)

        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=-geomtypes.FULL_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, geomtypes.UX)

        # 90 degrees (+/- 360)
        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=geomtypes.QUARTER_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, geomtypes.UY)

        q = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=geomtypes.QUARTER_TURN + geomtypes.FULL_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, geomtypes.UY)

        q = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=geomtypes.QUARTER_TURN - geomtypes.FULL_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, geomtypes.UY)

        # 180 degrees (+/- 360)
        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=geomtypes.HALF_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, -geomtypes.UX)

        q = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=geomtypes.HALF_TURN + geomtypes.FULL_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, -geomtypes.UX)

        q = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=geomtypes.HALF_TURN - geomtypes.FULL_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, -geomtypes.UX)

        # -90 degrees (+/- 360)
        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=-geomtypes.QUARTER_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, -geomtypes.UY)

        q = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=-geomtypes.QUARTER_TURN + geomtypes.FULL_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, -geomtypes.UY)

        q = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=-geomtypes.QUARTER_TURN - geomtypes.FULL_TURN)
        v = geomtypes.Vec3(geomtypes.UX)
        r = q*v
        self.assertEqual(r, -geomtypes.UY)

        # Quadrant geomtypes.I
        v3_2 = math.sqrt(3) / 2
        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=math.pi/3)
        v = geomtypes.UX + 3*geomtypes.UZ
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([0.5, v3_2, 3]))

        # Quadrant II
        q = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=geomtypes.HALF_TURN - math.pi/3)
        v = geomtypes.UX + 3*geomtypes.UZ
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-0.5, v3_2, 3]))

        # Quadrant III
        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=math.pi + math.pi/3)
        v = geomtypes.UX + 3*geomtypes.UZ
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-0.5, -v3_2, 3]))

        # Quadrant IV
        q = geomtypes.Rot3(axis=geomtypes.UZ, angle=- math.pi/3)
        v = geomtypes.UX + 3*geomtypes.UZ
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([0.5, -v3_2, 3]))

    def test_rotation_around_111(self):
        """Test rotation around (+/-1, +/-1, +/-1) vectors"""
        # 3D Quadrant geomtypes.I: rotation around (1, 1, 1): don't specify
        # normalise axis
        q = geomtypes.Rot3(axis=geomtypes.Vec3([1, 1, 1]),
                           angle=geomtypes.THIRD_TURN)
        v = geomtypes.Vec3([-1, 1, 1])
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, -1, 1]))
        # neg angle
        q = geomtypes.Rot3(axis=geomtypes.Vec3([1, 1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, 1, -1]))
        # neg axis, neg angle
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([1, 1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, -1, 1]))
        # neg axis
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([1, 1, 1]),
                           angle=geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, 1, -1]))

        # 3D Quadrant II: rotation around (-1, 1, 1): don't specify normalise
        # axis
        q = geomtypes.Rot3(axis=geomtypes.Vec3([-1, 1, 1]),
                           angle=geomtypes.THIRD_TURN)
        v = geomtypes.Vec3([1, 1, 1])
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, 1, -1]))
        # neg angle
        q = geomtypes.Rot3(axis=geomtypes.Vec3([-1, 1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, -1, 1]))
        # neg axis, neg angle
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([-1, 1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, 1, -1]))
        # neg axis
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([-1, 1, 1]),
                           angle=geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, -1, 1]))

        # 3D Quadrant III: rotation around (-1, 1, 1): don't specify normalise
        # axis
        q = geomtypes.Rot3(axis=geomtypes.Vec3([-1, -1, 1]),
                           angle=geomtypes.THIRD_TURN)
        v = geomtypes.Vec3([1, 1, 1])
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, 1, -1]))
        # neg angle
        q = geomtypes.Rot3(axis=geomtypes.Vec3([-1, -1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, -1, -1]))
        # neg axis, neg angle
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([-1, -1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, 1, -1]))
        # neg axis
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([-1, -1, 1]),
                           angle=geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, -1, -1]))

        # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise
        # axis
        q = geomtypes.Rot3(axis=geomtypes.Vec3([1, -1, 1]),
                           angle=geomtypes.THIRD_TURN)
        v = geomtypes.Vec3([1, 1, 1])
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, -1, 1]))
        # neg angle
        q = geomtypes.Rot3(axis=geomtypes.Vec3([1, -1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, -1, -1]))
        # neg axis, neg angle
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([1, -1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, -1, 1]))
        # neg axis
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([1, -1, 1]),
                           angle=geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, -1, -1]))

        # test quat mul from above (instead of geomtypes.Vec3):
        # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise
        # axis
        q = geomtypes.Rot3(axis=geomtypes.Vec3([1, -1, 1]),
                           angle=geomtypes.THIRD_TURN)
        v = geomtypes.Quat([0, 1, 1, 1])
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, -1, 1]))
        # neg angle
        q = geomtypes.Rot3(axis=geomtypes.Vec3([1, -1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, -1, -1]))
        # neg axis, neg angle
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([1, -1, 1]),
                           angle=-geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([-1, -1, 1]))
        # neg axis
        q = geomtypes.Rot3(axis=-geomtypes.Vec3([1, -1, 1]),
                           angle=geomtypes.THIRD_TURN)
        r = q*v
        self.assertEqual(r, geomtypes.Vec3([1, -1, -1]))

    def check_angle_axis(self, c1, c2, precision=10):
        """Check whether angle and axis specify the same rotation

        c1: tuple (angle, axis) to compare with c2
        c2: tuple (angle, axis) to compare with c1
        precision: number of decimal places to compare
        """
        a, x, = c1
        ra, rx = c2
        if rx == x:
            self.assertAlmostEqual(ra, a, precision)
        else:
            self.assertAlmostEqual(ra, -a, precision)
            self.assertEqual(rx, -x)

    def test_axis_angle(self):
        """Test getting axis / angle"""
        v = geomtypes.Vec3([1, -1, 1])
        a = geomtypes.THIRD_TURN
        t = geomtypes.Rot3(axis=v, angle=a)
        rx = t.axis()
        x = v.normalise()
        ra = t.angle()
        self.check_angle_axis((a, x), (ra, rx))
        self.assertTrue(t.is_rot())
        self.assertFalse(t.is_refl())
        self.assertFalse(t.is_rot_inv())
        self.assertEqual(t.type(), t.Rot)
        # neg angle
        v = geomtypes.Vec3([1, -1, 1])
        a = -geomtypes.THIRD_TURN
        t = geomtypes.Rot3(axis=v, angle=a)
        rx = t.axis()
        x = v.normalise()
        ra = t.angle()
        self.check_angle_axis((a, x), (ra, rx))
        self.assertTrue(t.is_rot())
        self.assertFalse(t.is_refl())
        self.assertFalse(t.is_rot_inv())
        self.assertEqual(t.type(), t.Rot)
        # neg angle, neg axis
        v = geomtypes.Vec3([-1, 1, -1])
        a = -geomtypes.THIRD_TURN
        t = geomtypes.Rot3(axis=v, angle=a)
        rx = t.axis()
        x = v.normalise()
        ra = t.angle()
        self.check_angle_axis((a, x), (ra, rx))
        self.assertTrue(t.is_rot())
        self.assertFalse(t.is_refl())
        self.assertFalse(t.is_rot_inv())
        self.assertEqual(t.type(), t.Rot)
        # neg axis
        v = geomtypes.Vec3([-1, 1, -1])
        a = geomtypes.THIRD_TURN
        t = geomtypes.Rot3(axis=v, angle=a)
        rx = t.axis()
        x = v.normalise()
        ra = t.angle()
        self.check_angle_axis((a, x), (ra, rx))
        self.assertTrue(t.is_rot())
        self.assertFalse(t.is_refl())
        self.assertFalse(t.is_rot_inv())
        self.assertEqual(t.type(), t.Rot)
        # quadrant I
        v = geomtypes.Vec3([-1, 1, -1])
        a = math.pi/3
        t = geomtypes.Rot3(axis=v, angle=a)
        rx = t.axis()
        x = v.normalise()
        ra = t.angle()
        self.check_angle_axis((a, x), (ra, rx))
        self.assertTrue(t.is_rot())
        self.assertFalse(t.is_refl())
        self.assertFalse(t.is_rot_inv())
        self.assertEqual(t.type(), t.Rot)
        # quadrant II
        v = geomtypes.Vec3([-1, 1, -1])
        a = math.pi - math.pi/3
        t = geomtypes.Rot3(axis=v, angle=a)
        rx = t.axis()
        x = v.normalise()
        ra = t.angle()
        self.check_angle_axis((a, x), (ra, rx))
        self.assertTrue(t.is_rot())
        self.assertFalse(t.is_refl())
        self.assertFalse(t.is_rot_inv())
        self.assertEqual(t.type(), t.Rot)
        # quadrant III
        v = geomtypes.Vec3([-1, 1, -1])
        a = math.pi + math.pi/3
        t = geomtypes.Rot3(axis=v, angle=a)
        rx = t.axis()
        x = v.normalise()
        ra = t.angle()
        a = a - 2 * math.pi
        self.check_angle_axis((a, x), (ra, rx))
        self.assertTrue(t.is_rot())
        self.assertFalse(t.is_refl())
        self.assertFalse(t.is_rot_inv())
        self.assertEqual(t.type(), t.Rot)
        # quadrant IV
        v = geomtypes.Vec3([-1, 1, -1])
        a = - math.pi/3
        t = geomtypes.Rot3(axis=v, angle=a)
        rx = t.axis()
        x = v.normalise()
        ra = t.angle()
        self.check_angle_axis((a, x), (ra, rx))
        self.assertTrue(t.is_rot())
        self.assertFalse(t.is_refl())
        self.assertFalse(t.is_rot_inv())
        self.assertEqual(t.type(), t.Rot)

        q = geomtypes.Quat([0, 0, 0, 0])
        with self.assertRaises(geomtypes.NoRotation):
            geomtypes.Rot3(q)

        # test equality for negative axis and negative angle
        r0 = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=2)
        r1 = geomtypes.Rot3(-r0[0])
        self.assertEqual(r0, r1)

    def test_order(self):
        """Test order of rotations"""
        # test order
        r0 = geomtypes.Rot3(axis=geomtypes.UZ, angle=geomtypes.QUARTER_TURN)
        r1 = geomtypes.Rot3(axis=geomtypes.UX, angle=geomtypes.QUARTER_TURN)
        r = (r1 * r0) * geomtypes.UX  # expected: r1(r0(x))
        self.assertEqual(r, geomtypes.UZ)
        r = r1 * r0
        x = geomtypes.Rot3(axis=geomtypes.Vec3([1, -1, 1]),
                           angle=geomtypes.THIRD_TURN)
        self.assertEqual(r, x)
        r = r0 * r1
        x = geomtypes.Rot3(axis=geomtypes.Vec3([1, 1, 1]),
                           angle=geomtypes.THIRD_TURN)
        self.assertEqual(r, x)

    def test_conversion_to_matrix(self):
        """Test converting to matrix"""
        # x-axis
        r = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=geomtypes.QUARTER_TURN).matrix()
        # 0  -1  0
        # 1   0  0
        # 0   0  1
        x = geomtypes.Vec3([0, -1, 0])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([1, 0, 0])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([0, 0, 1])
        self.assertEqual(r[2], x)
        r = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=geomtypes.HALF_TURN).matrix()
        # -1   0  0
        #  0  -1  0
        #  0   0  1
        x = geomtypes.Vec3([-1, 0, 0])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([0, -1, 0])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([0, 0, 1])
        self.assertEqual(r[2], x)
        r = geomtypes.Rot3(axis=geomtypes.UZ,
                           angle=-geomtypes.QUARTER_TURN).matrix()
        #  0   1  0
        # -1   0  0
        #  0   0  1
        x = geomtypes.Vec3([0, 1, 0])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([-1, 0, 0])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([0, 0, 1])
        self.assertEqual(r[2], x)

        # y-axis
        r = geomtypes.Rot3(axis=geomtypes.UY,
                           angle=geomtypes.QUARTER_TURN).matrix()
        #  0   0   1
        #  0   1   0
        # -1   0   0
        x = geomtypes.Vec3([0, 0, 1])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([0, 1, 0])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([-1, 0, 0])
        self.assertEqual(r[2], x)
        r = geomtypes.Rot3(axis=geomtypes.UY,
                           angle=geomtypes.HALF_TURN).matrix()
        # -1   0   0
        #  0   1   0
        #  0   0  -1
        x = geomtypes.Vec3([-1, 0, 0])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([0, 1, 0])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([0, 0, -1])
        self.assertEqual(r[2], x)
        r = geomtypes.Rot3(axis=geomtypes.UY,
                           angle=-geomtypes.QUARTER_TURN).matrix()
        #  0   0  -1
        #  0   1   0
        #  1   0   0
        x = geomtypes.Vec3([0, 0, -1])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([0, 1, 0])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([1, 0, 0])
        self.assertEqual(r[2], x)

        # x-axis
        r = geomtypes.Rot3(axis=geomtypes.UX,
                           angle=geomtypes.QUARTER_TURN).matrix()
        # 1  0  0
        # 0  0 -1
        # 0  1  0
        x = geomtypes.Vec3([1, 0, 0])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([0, 0, -1])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([0, 1, 0])
        self.assertEqual(r[2], x)
        r = geomtypes.Rot3(axis=geomtypes.UX,
                           angle=geomtypes.HALF_TURN).matrix()
        #  1  0  0
        #  0 -1  0
        #  0  0 -1
        x = geomtypes.Vec3([1, 0, 0])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([0, -1, 0])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([0, 0, -1])
        self.assertEqual(r[2], x)
        r = geomtypes.Rot3(axis=geomtypes.UX,
                           angle=-geomtypes.QUARTER_TURN).matrix()
        #  1  0  0
        #  0  0  1
        #  0 -1  0
        x = geomtypes.Vec3([1, 0, 0])
        self.assertEqual(r[0], x)
        x = geomtypes.Vec3([0, 0, 1])
        self.assertEqual(r[1], x)
        x = geomtypes.Vec3([0, -1, 0])
        self.assertEqual(r[2], x)

    def test_types(self):
        """Test type of transform"""
        random.seed(700114)  # constant seed for predictable behaviour
        for _ in range(100):
            r0 = geomtypes.Rot3(axis=[2*random.random()-1,
                                      2*random.random()-1,
                                      2*random.random()-1],
                                angle=random.random() * 2 * math.pi)
            r1 = geomtypes.Rot3(axis=[2*random.random()-1,
                                      2*random.random()-1,
                                      2*random.random()-1],
                                angle=random.random() * 2 * math.pi)
            r = r0 * r1
            assert r0.is_rot()
            assert not r0.is_refl()
            assert not r0.is_rot_inv()
            assert r1.is_rot()
            assert not r1.is_refl()
            assert not r1.is_rot_inv()
            assert r.is_rot()
            assert not r.is_refl()
            assert not r.is_rot_inv()
            self.assertEqual(r0 * r0.inverse(), geomtypes.E)
            self.assertEqual(r1 * r1.inverse(), geomtypes.E)
            self.assertEqual(r * r.inverse(), geomtypes.E)


class TestRefl3(unittest.TestCase):
    """Unit tests for geomtypes.Refl3"""

    def test_basic(self):
        """Some basic tests of geomtypes.Refl3"""
        q = geomtypes.Quat([0, 0, 0, 0])
        with self.assertRaises(AssertionError):
            geomtypes.Refl3(q)

        v = geomtypes.Vec3([0, 0, 0])
        with self.assertRaises(AssertionError):
            geomtypes.Refl3(normal=v)

        v = geomtypes.Vec([1, 0])
        with self.assertRaises(IndexError):
            geomtypes.Refl3(normal=v)

    def test_types(self):
        """Some tests checking types"""
        random.seed(700114)  # constant seed to be able to catch errors
        for k in range(100):
            s0 = geomtypes.Refl3(normal=geomtypes.Vec3([2*random.random()-1,
                                                        2*random.random()-1,
                                                        2*random.random()-1]))
            s1 = geomtypes.Refl3(normal=geomtypes.Vec3([2*random.random()-1,
                                                        2*random.random()-1,
                                                        2*random.random()-1]))
            r = s0 * s1
            assert not s0.is_rot()
            assert s0.is_refl()
            assert not s0.is_rot_inv(), f"for i = {k}: {s0}"
            assert not s1.is_rot()
            assert s1.is_refl()
            assert not s1.is_rot_inv()
            assert r.is_rot()
            assert not r.is_refl()
            assert not r.is_rot_inv()
            self.assertEqual((s0 * s0), geomtypes.E)
            self.assertEqual((s1 * s1), geomtypes.E)
            self.assertEqual(r * r.inverse(), geomtypes.E)

        # border cases
        s0 = geomtypes.Refl3(normal=geomtypes.UX)
        s1 = geomtypes.Refl3(normal=geomtypes.UY)
        r = s0 * s1
        assert r.is_rot()
        assert not r.is_refl()
        assert not r.is_rot_inv()
        self.assertEqual(r, geomtypes.HalfTurn3(axis=geomtypes.UZ))
        r = s1 * s0
        assert r.is_rot()
        assert not r.is_refl()
        assert not r.is_rot_inv()
        self.assertEqual(r, geomtypes.HalfTurn3(axis=geomtypes.UZ))

        s0 = geomtypes.Refl3(normal=geomtypes.UX)
        s1 = geomtypes.Refl3(normal=geomtypes.UZ)
        r = s0 * s1
        assert r.is_rot()
        assert not r.is_refl()
        assert not r.is_rot_inv()
        self.assertEqual(r, geomtypes.HalfTurn3(axis=geomtypes.UY))
        r = s1 * s0
        assert r.is_rot()
        assert not r.is_refl()
        assert not r.is_rot_inv()
        self.assertEqual(r, geomtypes.HalfTurn3(axis=geomtypes.UY))

        s0 = geomtypes.Refl3(normal=geomtypes.UY)
        s1 = geomtypes.Refl3(normal=geomtypes.UZ)
        r = s0 * s1
        assert r.is_rot()
        assert not r.is_refl()
        assert not r.is_rot_inv()
        self.assertEqual(r, geomtypes.HalfTurn3(axis=geomtypes.UX))
        r = s1 * s0
        assert r.is_rot()
        assert not r.is_refl()
        assert not r.is_rot_inv()
        self.assertEqual(r, geomtypes.HalfTurn3(axis=geomtypes.UX))

        s0 = geomtypes.Refl3(normal=geomtypes.UX)
        s1 = geomtypes.Refl3(normal=geomtypes.UY)
        s2 = geomtypes.Refl3(normal=geomtypes.UZ)
        r = s0 * s1 * s2
        assert not r.is_rot()
        assert not r.is_refl()
        assert r.is_rot_inv()
        assert r.is_rot_refl()
        self.assertEqual(r, geomtypes.I)

    def test_order(self):
        """Test order of reflections"""
        # test order: 2 refl planes with 45 degrees in between: 90 rotation
        s0 = geomtypes.Refl3(normal=geomtypes.Vec3([0, 3, 0]))
        s1 = geomtypes.Refl3(normal=geomtypes.Vec3([-1, 1, 0]))
        r = s1 * s0
        x = geomtypes.Rot3(axis=geomtypes.UZ, angle=geomtypes.QUARTER_TURN)
        self.assertEqual(r, x)
        r = s0 * s1
        x = geomtypes.Rot3(axis=geomtypes.UZ, angle=-geomtypes.QUARTER_TURN)
        self.assertEqual(r, x)

    def test_opposite_normals(self):
        """tests equal reflection for opposite normals"""
        random.seed(760117)  # constant seed to be able to catch errors
        for _ in range(100):
            n = geomtypes.Vec3([2*random.random()-1,
                                2*random.random()-1,
                                2*random.random()-1])
            s0 = geomtypes.Refl3(normal=n)
            s1 = geomtypes.Refl3(normal=-n)
            self.assertEqual(s0, s1)
            r = s0 * s1
            self.assertEqual(r, geomtypes.E)

    def test_same_plane(self):
        """test reflection in same plane: border cases"""
        border_cases = [geomtypes.UX, geomtypes.UY, geomtypes.UZ]
        for n in border_cases:
            s0 = geomtypes.Refl3(normal=n)
            s1 = geomtypes.Refl3(normal=-n)
            self.assertEqual(s0, s1)
            r = s0 * s1
            self.assertEqual(r, geomtypes.E)


class TestTransform(unittest.TestCase):
    """Unit tests for geomtypes.Transform3"""

    def test_json(self):
        """Test saving to and loading from JSON."""
        test_matrix = [
            # E
            geomtypes.E,
            geomtypes.Rot3(axis=geomtypes.UZ, angle=0),
            # Rotations
            geomtypes.Rot3(axis=geomtypes.UZ, angle=1),
            geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=0.5),
            geomtypes.HalfTurn3(axis=geomtypes.Vec3([1, 1, 1])),
            geomtypes.Rotx(math.pi / 3),
            geomtypes.Roty(math.pi / 4),
            geomtypes.Rotz(math.pi / 6),
            geomtypes.HX,
            geomtypes.HY,
            geomtypes.HZ,
            # Reflections
            geomtypes.Refl3(normal=geomtypes.UZ),
            geomtypes.Refl3(normal=geomtypes.Vec3([1, 2, 3])),
            # Rotary inversions
            geomtypes.RotInv3(axis=geomtypes.UZ, angle=1),
            geomtypes.RotInv3(axis=geomtypes.Vec3([1, 2, 3]), angle=0.5),
        ]
        test_vec = [
            geomtypes.Vec([0, 0, 0]),
            geomtypes.Vec([0, 0, 1]),
            geomtypes.Vec([0, 1, 1]),
            geomtypes.Vec([1, 1, 1]),
        ]
        for trfm_org in test_matrix:
            filename = os.path.join(DIR_PATH, "output", "test_transform.json")
            trfm_org.write_json_file(filename)
            # Increase float_precision which is used to save floats
            with geomtypes.FloatHandler(12):
                trfm_new = geomtypes.Transform3.from_json_file(filename)
            with geomtypes.FloatHandler(9):
                self.assertEqual(trfm_org, trfm_new)
                for v in test_vec:
                    self.assertEqual(trfm_new * v, trfm_org * v)


class TestRotInv3(unittest.TestCase):
    """Unit tests for geomtypes.RotInv3"""

    def test_types(self):
        """Test types of rotary inversion"""
        random.seed(700114)  # constant seed to be able to catch errors
        for _ in range(100):
            r0 = geomtypes.RotInv3(axis=[2*random.random()-1,
                                         2*random.random()-1,
                                         2*random.random()-1],
                                   angle=random.random() * 2 * math.pi)
            r1 = geomtypes.RotInv3(axis=[2*random.random()-1,
                                         2*random.random()-1,
                                         2*random.random()-1],
                                   angle=random.random() * 2 * math.pi)
            r = r0 * r1
            assert not r0.is_rot()
            assert not r0.is_refl()
            assert r0.is_rot_inv()
            assert not r1.is_rot()
            assert not r1.is_refl()
            assert r1.is_rot_inv()
            assert r.is_rot()
            assert not r.is_refl()
            assert not r.is_rot_inv()
            self.assertEqual(r0 * r0.inverse(), geomtypes.E)
            self.assertEqual(r1 * r1.inverse(), geomtypes.E)
            self.assertEqual(r * r.inverse(), geomtypes.E)


class TestRot4(unittest.TestCase):
    """Unit tests for geomtypes.Rot4"""

    def test_basic(self):
        """Some basic tests of geomtypes.Rot4"""
        r0 = geomtypes.Rot4(axialPlane=(geomtypes.Vec4([1, 0, 0, 0]),
                                        geomtypes.Vec4([0, 0, 0, 1])),
                            angle=math.pi/3)
        v = geomtypes.Vec4([10, 2, 0, 6])
        r = r0 * v
        x = geomtypes.Quat([v[0], 1, -math.sqrt(3), v[3]])
        with geomtypes.FloatHandler(14):
            self.assertEqual(r, x)

        random.seed(700114)  # constant seed to be able to catch errors
        for _ in range(100):
            x0 = geomtypes.Vec4([2*random.random()-1,
                                 2*random.random()-1,
                                 2*random.random()-1,
                                 2*random.random()-1])
            # make sure orthogonal: x0*x1 + y0*y1 + z0*z1 + w0*w1 == 0
            w, x, y = (2*random.random()-1,
                       2*random.random()-1,
                       2*random.random()-1)
            z = (-w * x0[0] - x * x0[1] - y * x0[2]) / x0[3]
            x1 = geomtypes.Vec4([w, x, y, z])
            r0 = geomtypes.Rot4(axialPlane=(x0, x1),
                                angle=random.random() * 2 * math.pi)
            x0 = geomtypes.Vec4([2*random.random()-1,
                                 2*random.random()-1,
                                 2*random.random()-1,
                                 2*random.random()-1])
            w, x, y = (2*random.random()-1,
                       2*random.random()-1,
                       2*random.random()-1)
            # make sure orthogonal: x0*x1 + y0*y1 + z0*z1 + w0*w1 == 0
            z = (-w * x0[0] - x * x0[1] - y * x0[2]) / x0[3]
            x1 = geomtypes.Vec4([w, x, y, z])
            r1 = geomtypes.Rot4(axialPlane=(x0, x1),
                                angle=random.random() * 2 * math.pi)
            r = r0 * r1
            assert r0.is_rot()
            # Check these as soon as they are implemented for Transform4
            # assert not r0.is_refl()
            # assert not r0.is_rot_inv()
            assert r1.is_rot()
            # assert not r1.is_refl()
            # assert not r1.is_rot_inv()
            assert r.is_rot()
            # assert not r.is_refl()
            # assert not r.is_rot_inv()
            # self.assertEqual(r0 * r0.inverse(), geomtypes.E
            # self.assertEqual(r1 * r1.inverse(), geomtypes.E
            # self.assertEqual(r * r.inverse(), geomtypes.E
            for n in range(1, 12):
                if n > 98:
                    precision = 12
                else:
                    precision = geomtypes.FLOAT_PRECISION
                r0 = geomtypes.Rot4(axialPlane=(x0, x1), angle=2 * math.pi / n)
                r = r0
                with geomtypes.FloatHandler(precision):
                    for j in range(1, n):
                        a = geomtypes.RoundedFloat(r.angle())
                        self.assertTrue(a == j * 2 * math.pi / n)
                        r = r0 * r
                    ra = geomtypes.RoundedFloat(r.angle())
                    self.assertTrue(ra in (0, 2 * math.pi))

    def test_vectors_in_axis(self):
        """test if vectors in axial plane are not changed."""
        v0 = geomtypes.Vec4([1, 1, 1, 0])
        v1 = geomtypes.Vec4([0, 0, 1, 1])
        v1 = v1.make_orthogonal_to(v0)
        r0 = geomtypes.Rot4(axialPlane=(v1, v0), angle=math.pi/5)
        with geomtypes.FloatHandler(14):
            for k in range(5):
                v = v0 + k * v1
                r = r0 * v
                self.assertEqual(v, r)
                v = k * v0 + v1
                r = r0 * v
                self.assertEqual(v, r)


class TestDoubleRot4(unittest.TestCase):
    """Unit tests for geomtypes.DoubleRot4"""

    def test_basic(self):
        """Some basic tests of geomtypes.DoubleRot4"""
        with geomtypes.FloatHandler(14):
            r0 = geomtypes.DoubleRot4(axialPlane=(geomtypes.Vec4([1, 0, 0, 0]),
                                                  geomtypes.Vec4([0, 0, 0, 1])),
                                      # 1/6 th and 1/8 th turn
                                      angle=(math.pi/3, math.pi/4))
            v = geomtypes.Vec4([6, 2, 0, 6])
            r = r0 * v
            x = geomtypes.Quat([0, 1, -math.sqrt(3), math.sqrt(72)])
            self.assertTrue(r0.is_rot())
            self.assertEqual(r, x)
            r = geomtypes.E
            for _ in range(23):
                r = r0 * r
                self.assertTrue(r.is_rot())
                ra = geomtypes.RoundedFloat(r.angle())
                self.assertFalse(ra in (0, 2 * math.pi))
            r = r0 * r
            self.assertTrue(r.is_rot())
            ra = geomtypes.RoundedFloat(r.angle())
            self.assertTrue(ra in (0, 2 * math.pi))

            r0 = geomtypes.DoubleRot4(axialPlane=(geomtypes.Vec4([1, 0, 0, 0]),
                                                  geomtypes.Vec4([0, 0, 0, 1])),
                                      # 1/6 th and 1/8 th turn:
                                      angle=(math.pi/4, math.pi/3))
            v = geomtypes.Vec4([6, 2, 2, 0])
            r = r0 * v
            x = geomtypes.Quat([3, math.sqrt(8), 0, 3*math.sqrt(3)])
            self.assertTrue(r0.is_rot())
            self.assertEqual(r, x)
            r = geomtypes.E
            for _ in range(23):
                r = r0 * r
                self.assertTrue(r.is_rot())
                ra = geomtypes.RoundedFloat(r.angle())
                self.assertFalse(ra in (0, 2 * math.pi))
            r = r0 * r
            self.assertTrue(r.is_rot())
            ra = geomtypes.RoundedFloat(r.angle())
            self.assertTrue(ra in (0, 2 * math.pi))


class TestMat(unittest.TestCase):
    """Unit tests for geomtypes.Mat"""

    def test_basic(self):
        """Some basic tests of geomtypes.Mat"""
        m = geomtypes.Mat([geomtypes.Vec([1, 2, 3]),
                           geomtypes.Vec([0, 2, 1]),
                           geomtypes.Vec([1, -1, 3])])

        p = m.rows
        q = m.cols

        self.assertEqual(m.det(), m.T().det())
        self.assertEqual(m, m.T().T())

        t = m.T()

        for k in range(p):
            r = m.rm_row(k)
            self.assertEqual(r.rows, p-1)
            self.assertEqual(r.cols, q)
            self.assertEqual(r, m.rm_row(-(p-k)))
            n = t.T()
            n.pop(k)
            self.assertEqual(r, n)

        for k in range(q):
            r = m.rm_col(k)
            self.assertEqual(r.rows, p)
            self.assertEqual(r.cols, q-1)
            self.assertEqual(r, m.rm_col(-(q-k)))
            t = m.T()
            t.pop(k)
            self.assertEqual(r, t.T())

        # don't want to test an orthogonal matrix, since then the inverse
        # method calls: det, rm_row, -Col, and transpose.
        self.assertFalse(m.orthogonal())
        m_i = m.inverse()
        self.assertEqual(m * m_i, geomtypes.Mat())
        self.assertEqual(m_i * m, geomtypes.Mat())
        b = geomtypes.Vec([1, 2, 3])
        self.assertEqual(m.solve(b), m_i * b)


class TestLine(unittest.TestCase):
    """Unit tests for geomtypes.Line"""

    def test_get_factor_at_std(self):
        """Test get_factor_at with some exact (integer) solutions"""
        test_matrix = {  # test_case: (point, vector, value, i, expected t)
            "2D line x int": (geomtypes.Vec([1, 2]), geomtypes.Vec([1, 1]), 0, 0, -1),
            "2D line y int": (geomtypes.Vec([1, 2]), geomtypes.Vec([1, 1]), 0, 1, -2),
            "3D line x int": (geomtypes.Vec([1, 2, 3]), geomtypes.Vec([1, 1, 1]), 0, 0, -1),
            "3D line y int": (geomtypes.Vec([1, 2, 3]), geomtypes.Vec([1, 1, 1]), 0, 1, -2),
            "3D line z int": (geomtypes.Vec([1, 2, 3]), geomtypes.Vec([1, 1, 1]), 0, 2, -3),
            "3D line z None": (geomtypes.Vec([1, 2, 3]), geomtypes.Vec([1, 1, 0]), 0, 2, None),
        }
        for case, (p0, v, c, i, expect) in test_matrix.items():
            line = geomtypes.Line(p0, v=v)
            result = line.get_factor_at(c, i)
            d = ", delta = {result - expect}" if result is not None and expect is not None else ""
            self.assertTrue(
                result == expect,
                f"Error for '{case}': {result} != {expect} (expected)" + d
            )

    def test_get_factor_at_margins(self):
        """Test get_factor_at with solutions where rounding is involved"""
        test_matrix = {  # test_case: (point, vector, value, i, expected t)
            "2D line x int": (geomtypes.Vec([1, 2]), geomtypes.Vec([1, 1]), 0, 0, -1.00009),
            "3D line x int": (geomtypes.Vec([1, 2, 3]), geomtypes.Vec([1, 1, 1]), 0, 0, -1.00009),
        }
        for case, (p0, v, c, i, expect) in test_matrix.items():
            line = geomtypes.Line(p0, v=v)
            result = line.get_factor_at(c, i)
            precision = 4
            with geomtypes.FloatHandler(precision):
                self.assertTrue(
                    result == expect,
                    f"Error for '{case}': delta: {result - expect} > 1 * 10^-{precision}"
                )
            precision = 5
            with geomtypes.FloatHandler(precision):
                self.assertFalse(
                    result == expect,
                    f"Error for '{case}': delta: {result - expect} < 1 * 10^-{precision}"
                )


if __name__ == '__main__':
    unittest.main()
