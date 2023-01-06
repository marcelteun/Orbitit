#!/usr/bin/env python
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not,
# check at http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# or write to the Free Software Foundation,
#------------------------------------------------------------------

from copy import copy
import math
import os
import unittest

from orbitit import geomtypes, isometry

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
IN_DIR = "expected"
OUT_DIR = "output"

class TestSubGroups(unittest.TestCase):
    """Unit test subgroups"""

    def _chk_groups(self, g_tst, g_exp):
        g_subs = g_tst.subgroups
        for g in g_subs:
            self.assertTrue(g in g_exp,
                            msg='Extra subgroup {} in {}'.format(g, g_tst))
        for g in g_exp:
            self.assertTrue(g in g_subs,
                            msg='Missing subgroup {} in {}'.format(g, g_tst))
        self.assertTrue(len(g_subs) == len(g_exp),
                        msg='Duplicates subgroups in {}'.format(
                            'expected' if len(g_exp) > len(g_subs) else g_tst))

    def test_c(self):
        """Test some subgroups of C"""
        # Test one even with even and odd divisors:
        h = isometry.C(12)
        expect = [
            # trivial:
            isometry.C(12),
            isometry.E,
            # all divisors Cn:
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
            # isometry.C(1) ~= E
        ]
        self._chk_groups(h, expect)
        # Test one odd
        h = isometry.C(15)
        expect = [
            # trivial:
            isometry.C(15),
            isometry.E,
            # all divisors Cn:
            isometry.C(5),
            isometry.C(3),
            # isometry.C(1) ~= E
        ]
        self._chk_groups(h, expect)
        # Test lower limit: n = 2, n = 1
        h = isometry.C(2)
        expect = [
            # trivial:
            isometry.C(2),
            isometry.E,
        ]
        self._chk_groups(h, expect)
        h = isometry.C(1)
        expect = [
            # trivial:
            # isometry.C(1) ~= E
            isometry.E,
        ]
        self._chk_groups(h, expect)

    def test_cnxi(self):
        """Test some subgroups in CnxI"""
        # Test one even with even and odd divisors:
        h = isometry.CxI(12)
        expect = [
            # trivial:
            isometry.CxI(12),
            isometry.E,
            # all divisors CnxI
            isometry.CxI(6),
            isometry.CxI(4),
            isometry.CxI(3),
            isometry.CxI(2),
            isometry.ExI,
            # all divisors Cn
            isometry.C(12),
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
            # C2nCn: all odd divisors:
            isometry.C2nC(3),
            # C2nCn: even divisors, only if divide is even
            isometry.C2nC(6),
            isometry.C2nC(2),
            isometry.C2nC(1),
        ]
        self._chk_groups(h, expect)
        # Test one odd with divisors:
        h = isometry.CxI(9)
        expect = [
            # trivial:
            isometry.CxI(9),
            isometry.E,
            # all divisors CnxI
            isometry.CxI(3),
            isometry.ExI,
            # all divisors Cn
            isometry.C(9),
            isometry.C(3),
        ]
        self._chk_groups(h, expect)

    def test_c2ncn(self):
        """Test some subgroups of C2nCn"""
        # Test one even with even and odd divisors:
        h = isometry.C2nC(12)
        expect = [
            # trivial:
            isometry.C2nC(12),
            isometry.E,
            # All Cn:
            isometry.C(12),
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
            # C2nCn:
            #  - don't add odd divisors: have refl
            #  - even divisor: add if (n/i) % 2 != 0
            isometry.C2nC(4),
            # CnxI: no subgroups, since:
            #  - even divisors have reflection
            #  - odd divisors: since n even, n / odd is even. I.e. not mapped
            #    on rotated one.
        ]
        self._chk_groups(h, expect)
        # Test one odd
        # Odd C2nCn have reflections
        h = isometry.C2nC(15)
        expect = [
            # trivial:
            isometry.C2nC(15),
            isometry.E,
            # All Cn:
            isometry.C(15),
            isometry.C(5),
            isometry.C(3),
            # C2nCn:
            #  - add all divisors, since all are odd (since n is odd)
            isometry.C2nC(5),
            isometry.C2nC(3),
            isometry.C2nC(1),
            # CnxI: no subgroups:
            #  - all divisors are odd (since n odd), i.e. no reflections
        ]
        self._chk_groups(h, expect)

    def test_d(self):
        """Test some subgroups of D"""
        # Test one even with even and odd divisors:
        h = isometry.D(12)
        expect = [
            # trivial:
            isometry.D(12),
            isometry.E,
            # all divisors Dn, Cn:
            isometry.D(6),
            isometry.D(4),
            isometry.D(3),
            isometry.D(2),
            # isometry.D(1) ~= C2
            isometry.C(12),
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
            # isometry.C(1) ~= E
        ]
        self._chk_groups(h, expect)
        # Test one odd
        h = isometry.D(15)
        expect = [
            # trivial:
            isometry.D(15),
            isometry.E,
            # all divisors Dn, Cn:
            isometry.D(5),
            isometry.D(3),
            isometry.D(1),  # ~= C2
            isometry.C(15),
            isometry.C(5),
            isometry.C(3),
            # isometry.C(1) ~= E
        ]
        self._chk_groups(h, expect)
        # Test lower limit: n = 2, n = 1
        h = isometry.D(2)
        expect = [
            # trivial:
            isometry.D(2),
            isometry.E,
            # all divisors Dn, Cn:
            #isometry.D(1),  # ~= C2
            isometry.C(2),
        ]
        self._chk_groups(h, expect)
        h = isometry.D(1)
        expect = [
            # trivial:
            isometry.C(2),
            #isometry.D(1),  # ~= C2
            isometry.E,
            # no divisors..
        ]
        self._chk_groups(h, expect)

    def test_dxi(self):
        """Test some subgroups of DxI"""
        # Test one even with even and odd divisors:
        h = isometry.DxI(12)
        expect = [
            # trivial:
            isometry.DxI(12),
            isometry.E,
            # all divisors D2nCn, Cn, Dn:
            isometry.DnC(12),
            isometry.DnC(6),
            isometry.DnC(4),
            isometry.DnC(3),
            isometry.DnC(2),
            # isometry.DnC(1) ~= C2C1
            isometry.D(12),
            isometry.D(6),
            isometry.D(4),
            isometry.D(3),
            isometry.D(2),
            # isometry.D(1) ~= C2
            isometry.C(12),
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
            # isometry.C(1) ~= E
            # even divisors: DnxI, CnxI
            isometry.DxI(6),
            isometry.DxI(4),
            isometry.DxI(2),
            isometry.CxI(12),
            isometry.CxI(6),
            isometry.CxI(4),
            isometry.CxI(2),
            # odd divisors: D2nDn, C2nCn
            isometry.D2nD(3),
            # D2nD(1) ~= D2C2
            isometry.C2nC(3),
            isometry.C2nC(1),
            # even divisors: D2nDn, C2nCn if 12/n even
            isometry.D2nD(6),
            isometry.D2nD(2),
            isometry.C2nC(6),
            isometry.C2nC(2),
        ]
        self._chk_groups(h, expect)
        # Test one odd
        # Odd C2nCn have reflections
        h = isometry.DxI(15)
        expect = [
            # trivial:
            isometry.DxI(15),
            isometry.E,
            # all divisors D2nCn, Cn, Dn:
            isometry.DnC(15),
            isometry.DnC(5),
            isometry.DnC(3),
            isometry.DnC(1),  # ~= C2C1
            isometry.D(15),
            isometry.D(5),
            isometry.D(3),
            isometry.D(1),  # ~= C2
            isometry.C(15),
            isometry.C(5),
            isometry.C(3),
            # isometry.C(1) ~= E
            # odd divisors: DnxI, CnxI
            isometry.DxI(5),
            isometry.DxI(3),
            isometry.DxI(1),  # ~= C2xI
            isometry.CxI(15),
            isometry.CxI(5),
            isometry.CxI(3),
            isometry.CxI(1),  # ~= ExI
            # no even divisors: no D2nDn or C2nCn
        ]
        self._chk_groups(h, expect)

    def test_d2ndn(self):
        """Test some subgroups of D2nDn"""
        # Test one even with even and odd divisors:
        h = isometry.D2nD(12)
        expect = [
            # trivial:
            isometry.D2nD(12),
            isometry.E,
            # all divisors D2nCn, Cn, Dn:
            isometry.DnC(12),
            isometry.DnC(6),
            isometry.DnC(4),
            isometry.DnC(3),
            isometry.DnC(2),
            isometry.DnC(1),  # ~= C2C1
            isometry.D(12),
            isometry.D(6),
            isometry.D(4),
            isometry.D(3),
            isometry.D(2),
            # isometry.D(1) ~= C2
            isometry.C(12),
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
            # isometry.C(1) ~= E
            # even divisors i if n/i odd: D2nDn, C2nCn
            isometry.D2nD(4),
            isometry.C2nC(12),
            isometry.C2nC(4),
            # no DxI, CxI
        ]
        self._chk_groups(h, expect)
        # Test one odd
        # Odd C2nCn have reflections
        h = isometry.D2nD(15)
        expect = [
            # trivial:
            isometry.D2nD(15),
            isometry.E,
            # all divisors D2nCn, Cn, Dn:
            isometry.DnC(15),
            isometry.DnC(5),
            isometry.DnC(3),
            # isometry.DnC(1),  # ~= C2C1
            isometry.D(15),
            isometry.D(5),
            isometry.D(3),
            isometry.D(1),  # ~= C2
            isometry.C(15),
            isometry.C(5),
            isometry.C(3),
            # isometry.C(1) ~= E
            # odd divisors: D2nDn or C2nCn
            isometry.D2nD(5),
            isometry.D2nD(3),
            isometry.D2nD(1),  # ~= D2C2
            isometry.C2nC(15),
            isometry.C2nC(5),
            isometry.C2nC(3),
            isometry.C2nC(1),  # ~= E + S
            # no DnxI, CnxI
        ]
        self._chk_groups(h, expect)

    def test_close(self):
        g = isometry.Set([geomtypes.HX, geomtypes.HY])
        self.assertTrue(geomtypes.Rot3(axis=[1, 0, 0], angle=geomtypes.HALF_TURN) in g)
        self.assertTrue(geomtypes.Rot3(axis=[-1, 0, 0], angle=-geomtypes.HALF_TURN) in g)
        self.assertFalse(geomtypes.HZ in g)
        self.assertFalse(geomtypes.E in g)
        cg = g.close()
        self.assertEqual(len(cg), 4)
        self.assertTrue(geomtypes.HX in cg)
        self.assertTrue(geomtypes.HY in cg)
        self.assertTrue(geomtypes.HZ in cg)
        self.assertTrue(geomtypes.E in cg)

        g = isometry.Set([geomtypes.Rot3(axis=geomtypes.UX, angle=geomtypes.QUARTER_TURN)])
        self.assertTrue(geomtypes.Rot3(axis=geomtypes.UX, angle=geomtypes.QUARTER_TURN)  in g)
        self.assertTrue(geomtypes.Rot3(axis=-geomtypes.UX, angle=-geomtypes.QUARTER_TURN) in g)
        cg = g.close()
        self.assertEqual(len(cg), 4)
        self.assertTrue(
            geomtypes.Rot3(axis=geomtypes.Vec3([1, 0, 0]), angle=geomtypes.QUARTER_TURN) in cg
        )
        self.assertTrue(
            geomtypes.Rot3(axis=-geomtypes.Vec3([1, 0, 0]), angle=-geomtypes.QUARTER_TURN) in cg
        )
        self.assertTrue(geomtypes.HX in cg)
        self.assertTrue(geomtypes.E in cg)

    def test_A4(self):
        a4 = isometry.A4(
            setup=isometry.init_dict(o2axis0=geomtypes.UX, o2axis1=geomtypes.UY)
        )
        self.assertEqual(len(a4), 12)
        self.assertTrue(geomtypes.E in a4)
        self.assertTrue(geomtypes.HX in a4)
        self.assertTrue(geomtypes.HY in a4)
        self.assertTrue(geomtypes.HZ in a4)
        transforms = [
            geomtypes.Rot3(axis=[1,  1,  1], angle=geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1,  1,  1], angle=2*geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, -1,  1], angle=geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, -1,  1], angle=2*geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, -1, -1], angle=geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, -1, -1], angle=2*geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1,  1, -1], angle=geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1,  1, -1], angle=2*geomtypes.THIRD_TURN),
        ]
        for t in transforms:
            self.assertTrue(t in a4)

        a4_alt = isometry.A4(
            setup = isometry.init_dict(
                # try list argument
                o2axis0=[1, 1, 1],
                # try Rot3 argument
                o2axis1=geomtypes.HalfTurn3(axis=[1, -1, 0]))
        )
        # this a4_alt is the same as the above a4 repositioned as follows:
        r0 = geomtypes.Rot3(axis = geomtypes.UZ, angle = geomtypes.QUARTER_TURN / 2)
        r1 = geomtypes.Rot3(axis = [1, -1, 0], angle = math.atan(1/math.sqrt(2)))
        r = r1 * r0
        self.assertEqual(len(a4_alt), 12)
        self.assertTrue(geomtypes.E in a4_alt)
        self.assertTrue(geomtypes.HalfTurn3(axis=r*geomtypes.UX) in a4_alt)
        self.assertTrue(geomtypes.HalfTurn3(axis=r*geomtypes.UY) in a4_alt)
        self.assertTrue(geomtypes.HalfTurn3(axis=r*geomtypes.UZ) in a4_alt)
        for t in transforms:
            self.assertTrue(
                geomtypes.Rot3(axis=r * t.axis(), angle=geomtypes.THIRD_TURN) in a4_alt
            )

        ca4 = copy(a4)
        a4.group(2)
        self.assertEqual(a4, ca4)

    def test_quotient_set(self):
        a4 = isometry.A4(
            setup=isometry.init_dict(o2axis0=geomtypes.UX, o2axis1=geomtypes.UY)
        )
        self.assertTrue(len(a4) == 12)
        d2 = isometry.Set([geomtypes.HX, geomtypes.HY])
        d2.group()
        self.assertTrue(len(d2) == 4)
        q = a4 / d2
        for s in q:
            self.assertTrue(len(s) == 4)
        self.assertTrue(len(q) == 3)
        # check if isometry.A4 / D2 is a partition of isometry.A4:
        for i in range(len(q)-1):
            s = q[i]
            for transform in s:
                for j in range(i+1, len(q)):
                    self.assertTrue(not transform in q[j])

    def test_quotient_set(self):
        s4 = isometry.S4()
        a4 = isometry.A4()
        self.assertTrue(a4.is_subgroup(s4))
        self.assertFalse(s4.is_subgroup(a4))
        a4.add(geomtypes.I)
        self.assertFalse(a4.is_subgroup(s4))

    def test_json_import_export(self):
        # sub_test_name, isometry
        isoms = [
            [ "E", isometry.E()],
            [ "A4", isometry.A4()],
            [ "A5", isometry.A5()],
            [ "S4", isometry.S4()],
            [ "ExI", isometry.ExI()],
            [ "S4A4", isometry.S4A4()],
            [ "A4xI", isometry.A4xI()],
            [ "A5xI", isometry.A5xI()],
            [ "S4xI", isometry.S4xI()],
            # std cyclic and dihedral groups:
            [ "C1", isometry.C1()],
            [ "C2", isometry.C2()],
            [ "C3", isometry.C3()],
            [ "C4", isometry.C4()],
            [ "C5", isometry.C5()],
            [ "D1", isometry.D1()],
            [ "D2", isometry.D2()],
            [ "D3", isometry.D3()],
            [ "D4", isometry.D4()],
            [ "D5", isometry.D5()],
            [ "C2C1", isometry.C2C1()],
            [ "C4C2", isometry.C4C2()],
            [ "C6C3", isometry.C6C3()],
            [ "C8C4", isometry.C8C4()],
            [ "C1xI", isometry.C1xI()],
            [ "C2xI", isometry.C2xI()],
            [ "C3xI", isometry.C3xI()],
            [ "C4xI", isometry.C4xI()],
            [ "C5xI", isometry.C5xI()],
            [ "D1C1", isometry.D1C1()],
            [ "D2C2", isometry.D2C2()],
            [ "D3C3", isometry.D3C3()],
            [ "D4C4", isometry.D4C4()],
            [ "D5C5", isometry.D5C5()],
            [ "D1xI", isometry.D1xI()],
            [ "D2xI", isometry.D2xI()],
            [ "D3xI", isometry.D3xI()],
            [ "D4xI", isometry.D4xI()],
            [ "D5xI", isometry.D5xI()],
            [ "D2D1", isometry.D2D1()],
            [ "D4D2", isometry.D4D2()],
            [ "D6D3", isometry.D6D3()],
            [ "D8D4", isometry.D8D4()],
            # TODO: newly created cyclic and dihedral groups
            [ "D10D5", isometry.D2nD(5)()],
            [ "C10C5", isometry.C2nC(5)()],
        ]
        for name, isom in isoms:
            filename = os.path.join(DIR_PATH, OUT_DIR, f"check_isom_{name}.json")
            isom.write_json_file(filename)
            isom_cp = isometry.Set.from_json_file(filename)
            self.assertEqual(isom, isom_cp)
            cmp_filename = os.path.join(DIR_PATH, IN_DIR, f"check_isom_{name}.json")
            # Set to True to generate the expected files. This requires a manual check then
            regenerate_in_files = False
            if regenerate_in_files:
                rm_generator = isometry.Set([i for i in isom])
                rm_generator.write_json_file(cmp_filename)
            isom_cmp = isometry.Set.from_json_file(cmp_filename)
            self.assertEqual(isom, isom_cmp)


if __name__ == '__main__':
    unittest.main()
    print('success!')
