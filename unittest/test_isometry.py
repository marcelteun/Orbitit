#!/usr/bin/env python
"""Unit test the file isometry.py"""
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
# ------------------------------------------------------------------

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

    def _chk_groups(self, test_name, g_tst, g_exp):
        """Compare whether the two sets of subgroups are the same."""
        g_subs = g_tst.subgroups
        for g in g_subs:
            self.assertTrue(
                g in g_exp, msg=f"{test_name}: extra subgroup {g} in {g_tst}"
            )
        for g in g_exp:
            self.assertTrue(
                g in g_subs, msg=f"{test_name}: missing subgroup {g} in {g_tst}"
            )
        bigger_group_str = "expected" if len(g_exp) > len(g_subs) else g_tst
        self.assertTrue(
            len(g_subs) == len(g_exp),
            f"{test_name}: Duplicates subgroups in {bigger_group_str}",
        )

    def test_subgroups_per_class(self):
        """Test subgroups of dihedral and cyclic class at the class level"""
        test_matrix = {}
        # key: test ID
        # values: class_under_test, expected_sub_groups

        #############################################
        # Cn                                        #
        #############################################
        test_matrix["test_Cn_even_n"] = [
            isometry.C(12),
            [
                # trivial:
                isometry.C(12),
                isometry.E,
                # all divisors Cn:
                isometry.C(6),
                isometry.C(4),
                isometry.C(3),
                isometry.C(2),
                # isometry.C(1) ~= E
            ],
        ]
        test_matrix["test_Cn_odd_n"] = [
            isometry.C(15),
            [
                # trivial:
                isometry.C(15),
                isometry.E,
                # all divisors Cn:
                isometry.C(5),
                isometry.C(3),
                # isometry.C(1) ~= E
            ],
        ]
        test_matrix["test_Cn_lowest_n_even"] = [
            isometry.C(2),
            [
                # trivial:
                isometry.C(2),
                isometry.E,
            ],
        ]
        test_matrix["test_Cn_lowest_n_odd"] = [
            isometry.C(1),
            [
                # trivial:
                # isometry.C(1) ~= E
                isometry.E,
            ],
        ]
        #############################################
        # CnxI                                      #
        #############################################
        test_matrix["test_CnxI_even_n_with_odd_divisors"] = [
            isometry.CxI(12),
            [
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
            ],
        ]
        # Test one odd with divisors:
        test_matrix["test_CnxI_odd_n"] = [
            isometry.CxI(9),
            [
                # trivial:
                isometry.CxI(9),
                isometry.E,
                # all divisors CnxI
                isometry.CxI(3),
                isometry.ExI,
                # all divisors Cn
                isometry.C(9),
                isometry.C(3),
            ],
        ]

        #############################################
        # C2nCn                                     #
        #############################################
        test_matrix["test_C2nCn_even_n_with_odd_divisors"] = [
            isometry.C2nC(12),
            [
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
            ],
        ]
        test_matrix["test_C2nCn_odd_n"] = [
            # Odd C2nCn have reflections
            isometry.C2nC(15),
            [
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
            ],
        ]

        #############################################
        # Dn                                        #
        #############################################
        test_matrix["test_Dn_even_n_with_odd_divisors"] = [
            isometry.D(12),
            [
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
            ],
        ]
        test_matrix["test_Dn_odd_n"] = [
            isometry.D(15),
            [
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
            ],
        ]
        test_matrix["test_Dn_lowest_n_even"] = [
            isometry.D(2),
            [
                # trivial:
                isometry.D(2),
                isometry.E,
                # all divisors Dn, Cn:
                # isometry.D(1),  # ~= C2
                isometry.C(2),
            ],
        ]
        test_matrix["test_Dn_lowest_n_odd"] = [
            isometry.D(1),
            [
                # trivial:
                isometry.C(2),
                # isometry.D(1),  # ~= C2
                isometry.E,
                # no divisors..
            ],
        ]

        #############################################
        # DnxI                                      #
        #############################################
        test_matrix["test_DnxI_even_n_with_odd_divisors"] = [
            isometry.DxI(12),
            [
                # trivial:
                isometry.DxI(12),
                isometry.E,
                isometry.ExI,
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
                isometry.DxI(3),
                isometry.DxI(2),
                isometry.CxI(12),
                isometry.CxI(6),
                isometry.CxI(4),
                isometry.CxI(3),
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
            ],
        ]
        test_matrix["test_DnxI_odd_n"] = [
            isometry.DxI(15),
            [
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
            ],
        ]

        #############################################
        # D2nDn                                     #
        #############################################
        test_matrix["test_D2nDn_even_n_with_odd_divisors"] = [
            isometry.D2nD(12),
            [
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
            ],
        ]
        test_matrix["test_D2nDn_odd_n"] = [
            isometry.D2nD(15),
            [
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
            ],
        ]

        for test_name, (class_to_test, expect) in test_matrix.items():
            self._chk_groups(test_name, class_to_test, expect)

    def _subgroups_per_object(
        self,
        test_name,
        test_class,
        subgroup_class,
        class_setup=None,
        subgroup_setup=None,
    ):
        """General test function for testin <class>_get_subgroup funcitons

        This test can check the rules that are applied by actually creating a subgroup and checking
        the isometries directly in that functions and whether more subgroups exist.

        test_name: test name to show when test fails
        test_class: class to test
        subgroup_class: the subgroup class to test for
        setup_class: if defined the setup parameter for test_class
        setup_subgroup: if defined the setup parameter for subgroup
        """
        # Optionally one can define a setup and check if the setup is define in test_data
        test_obj = test_class(setup=class_setup)
        test_subgroup = subgroup_class(setup=subgroup_setup)
        is_subgroup = True
        for isom in test_subgroup:
            if isom not in test_obj:
                is_subgroup = False
                break
        if is_subgroup != (subgroup_class in test_class.subgroups):
            if is_subgroup:
                self.fail(
                    f"{test_name}: Missing subgroup {subgroup_class} in {test_class}"
                )
            else:
                self.fail(
                    f"{test_name}: False subgroup {subgroup_class} in {test_class} "
                    "or missmatching orientations"
                )

    def test_cn_ext_get_subgroups(self):
        """Test extended cyclic subgroups at the object level by actual checking with practice.

        Test _cnxi_get_subgroups and _c2ncn_get_subgroups in practice.

        This test can check the rules that are applied by actually creating a subgroup and checking
        the isometries directly in that functions and whether more subgroups exist.
        """
        test_matrix = {}
        for d_class in (isometry.CxI, isometry.C2nC):
            class_name = d_class.__name__
            test_n_12 = d_class(12)
            test_n_15 = d_class(15)
            test_matrix[f"CmxI in {class_name} with n and m even"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C4xI,
            }
            test_matrix[f"CmxI in {class_name} with n even and m odd"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C3xI,
            }
            test_matrix[f"CmxI in {class_name} with n and m a divisor of n"] = {
                "class": test_n_15,
                "subgroup_class": isometry.C3xI,
            }
            test_matrix[f"C2mCm in {class_name} with n even and n/m even"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C6C3,
            }
            test_matrix[f"C2mCm in {class_name} with n even and n/m odd"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C8C4,
            }
            test_matrix[f"C2mCm in {class_name} with n and m a divisor of n"] = {
                "class": test_n_15,
                "subgroup_class": isometry.C6C3,
            }

            for test_name, test_data in test_matrix.items():
                self._subgroups_per_object(
                    test_name,
                    test_data["class"],
                    test_data["subgroup_class"],
                    test_data.get("class_setup"),
                    test_data.get("subgroup_setup"),
                )

    def test_dn_ext_get_subgroups(self):
        """Test extended dihedral subgroups at the object level by actual checking with practice.

        Test _dnxi_get_subgroups and _d2ndn_get_subgroups in practice.

        This test can check the rules that are applied by actually creating a subgroup and checking
        the isometries directly in that functions and whether more subgroups exist.
        """
        test_matrix = {}
        for d_class in (isometry.DxI, isometry.D2nD):
            class_name = d_class.__name__
            test_n_12 = d_class(12)
            test_n_15 = d_class(15)
            test_matrix[f"CmxI in {class_name} with n and m even"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C4xI,
            }
            test_matrix[f"CmxI in {class_name} with n even and m odd"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C3xI,
            }
            test_matrix[f"CmxI in {class_name} with n and m a divisor of n"] = {
                "class": test_n_15,
                "subgroup_class": isometry.C3xI,
            }
            test_matrix[f"DmxI in {class_name} with n and m even"] = {
                "class": test_n_12,
                "subgroup_class": isometry.D4xI,
            }
            test_matrix[f"DmxI in {class_name} with n even and m odd"] = {
                "class": test_n_12,
                "subgroup_class": isometry.D3xI,
            }
            test_matrix[f"DmxI in {class_name} with n and m a divisor of n"] = {
                "class": test_n_15,
                "subgroup_class": isometry.D3xI,
            }
            test_matrix[f"C2mxI in {class_name} with n even and n/m even"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C3xI,
            }
            test_matrix[f"C2mxI in {class_name} with n even and n/m odd"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C4xI,
            }
            test_matrix[f"C2mxI in {class_name} with n and m a divisor of n"] = {
                "class": test_n_15,
                "subgroup_class": isometry.C3xI,
            }
            test_matrix[f"C2mCm in {class_name} with n even and n/m even"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C6C3,
            }
            test_matrix[f"C2mCm in {class_name} with n even and n/m odd"] = {
                "class": test_n_12,
                "subgroup_class": isometry.C8C4,
            }
            test_matrix[f"C2mCm in {class_name} with n and m a divisor of n"] = {
                "class": test_n_15,
                "subgroup_class": isometry.C6C3,
            }
            test_matrix[f"D2mDm in {class_name} with n even and n/m even"] = {
                "class": test_n_12,
                "subgroup_class": isometry.D6D3,
            }
            test_matrix[f"D2mDm in {class_name} with n even and n/m odd"] = {
                "class": test_n_12,
                "subgroup_class": isometry.D8D4,
            }
            test_matrix[f"D2mDm in {class_name} with n odd and m a divisor of n"] = {
                "class": test_n_15,
                "subgroup_class": isometry.D6D3,
            }

            for test_name, test_data in test_matrix.items():
                self._subgroups_per_object(
                    test_name,
                    test_data["class"],
                    test_data["subgroup_class"],
                    test_data.get("class_setup"),
                    test_data.get("subgroup_setup"),
                )

    def test_close(self):
        """Test closing the set of an isometries by adding the missing symmetries."""
        g = isometry.Set([geomtypes.HX, geomtypes.HY])
        self.assertTrue(geomtypes.Rot3(axis=[1, 0, 0], angle=geomtypes.HALF_TURN) in g)
        self.assertTrue(
            geomtypes.Rot3(axis=[-1, 0, 0], angle=-geomtypes.HALF_TURN) in g
        )
        self.assertFalse(geomtypes.HZ in g)
        self.assertFalse(geomtypes.E in g)
        cg = g.close()
        self.assertEqual(len(cg), 4)
        self.assertTrue(geomtypes.HX in cg)
        self.assertTrue(geomtypes.HY in cg)
        self.assertTrue(geomtypes.HZ in cg)
        self.assertTrue(geomtypes.E in cg)

        g = isometry.Set(
            [geomtypes.Rot3(axis=geomtypes.UX, angle=geomtypes.QUARTER_TURN)]
        )
        self.assertTrue(
            geomtypes.Rot3(axis=geomtypes.UX, angle=geomtypes.QUARTER_TURN) in g
        )
        self.assertTrue(
            geomtypes.Rot3(axis=-geomtypes.UX, angle=-geomtypes.QUARTER_TURN) in g
        )
        cg = g.close()
        self.assertEqual(len(cg), 4)
        self.assertTrue(
            geomtypes.Rot3(axis=geomtypes.Vec3([1, 0, 0]), angle=geomtypes.QUARTER_TURN)
            in cg
        )
        self.assertTrue(
            geomtypes.Rot3(
                axis=-geomtypes.Vec3([1, 0, 0]), angle=-geomtypes.QUARTER_TURN
            )
            in cg
        )
        self.assertTrue(geomtypes.HX in cg)
        self.assertTrue(geomtypes.E in cg)

    def test_a4(self):
        """Test the isometries of the A4 symmetry group."""
        a4 = isometry.A4(
            setup=isometry.init_dict(o2axis0=geomtypes.UX, o2axis1=geomtypes.UY)
        )
        self.assertEqual(len(a4), 12)
        self.assertTrue(geomtypes.E in a4)
        self.assertTrue(geomtypes.HX in a4)
        self.assertTrue(geomtypes.HY in a4)
        self.assertTrue(geomtypes.HZ in a4)
        transforms = [
            geomtypes.Rot3(axis=[1, 1, 1], angle=geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, 1, 1], angle=2 * geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, -1, 1], angle=geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, -1, 1], angle=2 * geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, -1, -1], angle=geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, -1, -1], angle=2 * geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, 1, -1], angle=geomtypes.THIRD_TURN),
            geomtypes.Rot3(axis=[1, 1, -1], angle=2 * geomtypes.THIRD_TURN),
        ]
        for t in transforms:
            self.assertTrue(t in a4)

        a4_alt = isometry.A4(
            setup=isometry.init_dict(
                # try list argument
                o2axis0=[1, 1, 1],
                # try Rot3 argument
                o2axis1=geomtypes.HalfTurn3(axis=[1, -1, 0]),
            )
        )
        # this a4_alt is the same as the above a4 repositioned as follows:
        r0 = geomtypes.Rot3(axis=geomtypes.UZ, angle=geomtypes.QUARTER_TURN / 2)
        r1 = geomtypes.Rot3(axis=[1, -1, 0], angle=math.atan(1 / math.sqrt(2)))
        r = r1 * r0
        self.assertEqual(len(a4_alt), 12)
        self.assertTrue(geomtypes.E in a4_alt)
        self.assertTrue(geomtypes.HalfTurn3(axis=r * geomtypes.UX) in a4_alt)
        self.assertTrue(geomtypes.HalfTurn3(axis=r * geomtypes.UY) in a4_alt)
        self.assertTrue(geomtypes.HalfTurn3(axis=r * geomtypes.UZ) in a4_alt)
        for t in transforms:
            self.assertTrue(
                geomtypes.Rot3(axis=r * t.axis(), angle=geomtypes.THIRD_TURN) in a4_alt
            )

        ca4 = copy(a4)
        a4.group(2)
        self.assertEqual(a4, ca4)

    def test_quotient_set(self):
        """Test a quotient set example."""
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
        for i in range(len(q) - 1):
            s = q[i]
            for transform in s:
                for j in range(i + 1, len(q)):
                    self.assertTrue(transform not in q[j])

    def test_some_std_sub_groups(self):
        """Test some standard subgroups."""
        a4 = isometry.A4()
        a4xi = isometry.A4xI()
        s4 = isometry.S4()
        s4xi = isometry.S4xI()
        a5 = isometry.A5()
        a5xi = isometry.A5xI()
        self.assertTrue(a4.is_subgroup(a4))
        self.assertTrue(a4.is_subgroup(a4xi))
        self.assertTrue(a4.is_subgroup(s4))
        self.assertTrue(a4.is_subgroup(a5))
        self.assertFalse(s4.is_subgroup(a4))
        self.assertTrue(s4.is_subgroup(s4))
        self.assertFalse(s4.is_subgroup(a5))
        self.assertTrue(a4xi.is_subgroup(a4xi))
        self.assertTrue(a4xi.is_subgroup(s4xi))
        self.assertTrue(a4xi.is_subgroup(a5xi))
        self.assertFalse(a4xi.is_subgroup(a5))
        self.assertTrue(a4xi.is_subgroup(a5xi))
        # Turn A4 into A4xI
        a4.add(geomtypes.I)
        self.assertFalse(a4.is_subgroup(s4))
        self.assertFalse(a4.is_subgroup(a5))
        self.assertFalse(a4.is_subgroup(a5xi))

    def test_json_import_export(self):
        """Test exporting and importing of an isometry to a JSON file"""
        isoms = [
            ["E", isometry.E()],
            ["A4", isometry.A4()],
            ["A5", isometry.A5()],
            ["S4", isometry.S4()],
            ["ExI", isometry.ExI()],
            ["S4A4", isometry.S4A4()],
            ["A4xI", isometry.A4xI()],
            ["A5xI", isometry.A5xI()],
            ["S4xI", isometry.S4xI()],
            # std cyclic and dihedral groups:
            ["C1", isometry.C1()],
            ["C2", isometry.C2()],
            ["C3", isometry.C3()],
            ["C4", isometry.C4()],
            ["C5", isometry.C5()],
            ["D1", isometry.D1()],
            ["D2", isometry.D2()],
            ["D3", isometry.D3()],
            ["D4", isometry.D4()],
            ["D5", isometry.D5()],
            ["C2C1", isometry.C2C1()],
            ["C4C2", isometry.C4C2()],
            ["C6C3", isometry.C6C3()],
            ["C8C4", isometry.C8C4()],
            ["C1xI", isometry.C1xI()],
            ["C2xI", isometry.C2xI()],
            ["C3xI", isometry.C3xI()],
            ["C4xI", isometry.C4xI()],
            ["C5xI", isometry.C5xI()],
            ["D1C1", isometry.D1C1()],
            ["D2C2", isometry.D2C2()],
            ["D3C3", isometry.D3C3()],
            ["D4C4", isometry.D4C4()],
            ["D5C5", isometry.D5C5()],
            ["D1xI", isometry.D1xI()],
            ["D2xI", isometry.D2xI()],
            ["D3xI", isometry.D3xI()],
            ["D4xI", isometry.D4xI()],
            ["D5xI", isometry.D5xI()],
            ["D2D1", isometry.D2D1()],
            ["D4D2", isometry.D4D2()],
            ["D6D3", isometry.D6D3()],
            ["D8D4", isometry.D8D4()],
            # TODO: newly created cyclic and dihedral groups
            ["D10D5", isometry.D2nD(5)()],
            ["C10C5", isometry.C2nC(5)()],
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
                rm_generator = isometry.Set(isom.copy())
                rm_generator.write_json_file(cmp_filename)
            isom_cmp = isometry.Set.from_json_file(cmp_filename)
            self.assertEqual(isom, isom_cmp)


if __name__ == "__main__":
    unittest.main()
    print("success!")
