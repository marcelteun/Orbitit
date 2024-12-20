#!/usr/bin/env python
"""Classes to create compounds of polyhedra with tetrahedron symmetry.

All base elements should be positioned with the synnetries as the standard
tetrahedron below.
"""
#
# Copyright (C) 2010-2024 Marcel Tunnissen
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
# -----------------------------------------------------------------
# Disable some pylint:
#     The class naming follows the group algebra names instead
# pylint: disable=invalid-name,too-many-arguments

import math

from orbitit import geomtypes, isometry, orbit
from orbitit.compounds import angle

V2 = math.sqrt(2)
V5 = math.sqrt(5)


class Compound(orbit.Shape):
    """A compound object, see orbit.Shape class for more info."""

    alt_base_pos = geomtypes.Rot3(axis=geomtypes.Vec3([0, 0, 1]), angle=math.pi / 4)


###############################################################################
#
# A4
#
###############################################################################
class A4_E(Compound):
    """General compound with A4 symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with A4 symmetry with central freedom."""
        super().__init__(
            base,
            isometry.A4(),
            isometry.E(),
            name="A4_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class A4_C3(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [-math.pi / 3, math.pi / 3, angle.D_ATAN_V3_2_V5]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 4 elements with final symmetry A4 (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.A4(),
            isometry.C3(setup={"axis": axis}),
            name="A4_C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        # Note double domain to show laevo and dextro
        self.set_rot_axis(axis, self.mu[:2])


###############################################################################
#
# A4 x I
#
###############################################################################
class A4xI_E(Compound):
    """General compound with A4xI symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with A4xI symmetry with central freedom."""
        super().__init__(
            base,
            isometry.A4xI(),
            isometry.E(),
            name="A4xI_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class A4xI_C3(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 3, angle.D_ATAN_V3_2_V5]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 8 elements with final symmetry A4xI (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.A4xI(),
            isometry.C3(setup={"axis": axis}),
            name="A4xI_C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


class A4xI_C2C1(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 4, angle.ASIN_1_V3]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 12 elements with final symmetry A4xI (rotation freedom)

        The descriptive shares a reflection plane with the final symmetry
        """
        axis = geomtypes.Vec3([1, 0, 0])
        super().__init__(
            base,
            isometry.A4xI(),
            isometry.C2C1(setup={"axis": axis}),
            name="A4xI_C2C1",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.transform_base(self.alt_base_pos)
        self.set_rot_axis(axis, self.mu[:2])


###############################################################################
#
# S4A4
#
###############################################################################
class S4A4_E(Compound):
    """General compound with S4A4 symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with S4A4 symmetry with central freedom."""
        super().__init__(
            base,
            isometry.S4A4(),
            isometry.E(),
            name="S4A4_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class S4A4_C4C2(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 4]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 6 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a order 2 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.S4A4(),
            isometry.C4C2(setup={"axis": axis}),
            name="S4A4_C4C2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


class S4A4_C3(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 3, math.pi / 6, angle.ACOS_1_V3]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 8 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.S4A4(),
            isometry.C3(setup={"axis": axis}),
            name="S4A4_C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


class S4A4_C2C1(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, 2 * angle.ASIN_1_V3, math.pi / 2, angle.ACOS_1_V3]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 12 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a reflection plane with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super().__init__(
            base,
            isometry.S4A4(),
            isometry.C2C1(setup={"axis": axis}),
            name="S4A4_C2C1",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:3])


# Rigid Compounds
class S4A4_S4A4(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Trivial "compound" of 1 element with final symmetry S4A4

        The descriptive shares all symmetries with the final one.
        """
        super().__init__(
            base,
            isometry.S4A4(),
            isometry.S4A4(),
            name="S4A4_S4A4",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class S4A4_D3C3(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid compound of 4 elements with S4A4 symmetry"""
        # Same as S4A4_C3 with special mu = 60 degrees
        axis = geomtypes.Vec3([1, 1, 1])
        normal = geomtypes.Vec3([-1, 1, 0])
        super().__init__(
            base,
            isometry.S4A4(),
            isometry.D3C3(setup={"axis_n": axis, "normal_r": normal}),
            name="S4A4_D3C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        # Move to rigid angle
        base_rot = geomtypes.Rot3(axis=axis, angle=math.pi / 3)
        self.transform_base(base_rot)


###############################################################################
#
# S4
#
###############################################################################
class S4_E(Compound):
    """General compound with S4 symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with S4 symmetry with central freedom."""
        super().__init__(
            base,
            isometry.S4(),
            isometry.E(),
            name="S4_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class S4_C3(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [-math.pi / 3, math.pi / 3, math.pi / 6, angle.D_ATAN_V3_2_V5]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 8 elements with final symmetry S4 (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.S4(),
            isometry.C3(setup={"axis": axis}),
            name="S4_C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        # Note double domain to show laevo and dextro
        self.set_rot_axis(axis, self.mu[:2])


class S4_C2(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        -math.pi / 4,
        math.pi / 4,
        angle.ATAN_3_2V2,
        angle.ASIN_1_V3,
        2 * angle.ATAN_3_2V2,
        angle.ATAN_H_V2_1_V5__1,
        angle.ATAN_H_V2_1_V5_1,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 12 elements with final symmetry S4 (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry (a pure
        2-fold axis, i.e. not a 4-fold axis)
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super().__init__(
            base,
            isometry.S4(),
            isometry.C2(setup={"axis": axis}),
            name="S4_C2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        # Note double domain to show laevo and dextro
        self.set_rot_axis(axis, self.mu[:2])

        self.transform_base(self.alt_base_pos)


###############################################################################
#
# S4 x I
#
###############################################################################
class S4xI_E(Compound):
    """General compound with S4xI symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with S4xI symmetry with central freedom."""
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.E(),
            name="S4xI_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class S4xI_C4C2(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 4, math.pi / 8]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 12 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 2-fold axis with the 4-fold axis in the final
        symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C4C2(setup={"axis": axis}),
            name="S4xI_C4C2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


class S4xI_C3(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 3, math.pi / 6, angle.D_ATAN_V3_2_V5]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 16 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C3(setup={"axis": axis}),
            name="S4xI_C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


class S4xI_C2(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        math.pi / 4,
        angle.ACOS_1_V3 - math.pi / 4,
        angle.ASIN_1_V3,
        math.pi / 8,
        angle.ATAN_4V2_7 / 2,
        angle.ATAN_H_V2_1_V5__1,
        angle.ATAN_H_V2_1_V5_1,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 24 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry (a pure
        2-fold axis, i.e. not a 4-fold axis)
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C2(setup={"axis": axis}),
            name="S4xI_C2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])
        self.transform_base(self.alt_base_pos)


class S4xI_C2C1(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        2 * angle.ASIN_1_V3,
        math.pi / 2,
        angle.ASIN_1_V3,
        angle.ACOS_1_V3,
        math.pi / 4,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 24 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a reflection plane with one from the final
        symmetry in such a way that the normal of the reflection plane goes
        through a pure 2-fold axis of the final symmetry.
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C2C1(setup={"axis": axis}),
            name="S4xI_C2C1",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:3])


class S4xI_D1C1(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        math.pi / 4,
        angle.ATAN_V2_4 / 2,
        angle.ATAN_V2_4,
        math.pi / 8,
        angle.ASIN_1_V3,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 24 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a reflection plane with one from the final
        symmetry in such a way that the normal of the reflection plane goes
        through a 4-fold axis of the final symmetry.
        """
        axis = geomtypes.Vec3([1, 0, 0])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.D1C1(setup={"axis": axis}),
            name="S4xI_D1C1",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])

        self.transform_base(self.alt_base_pos)


# Rigid Compounds
class S4xI_S4A4(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 2 elements with final symmetry S4xI

        With the orginisation as the classical Stella Octangula.
        """
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.S4A4(),
            name="S4xI_S4A4",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class S4xI_D4D2(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 6 elements with final symmetry S4xI

        With the orginisation as the classical compound of 3 cubes, but by
        replacing each cube by a Stella Octangula.
        """
        axis_n = geomtypes.Vec3([0, 0, 1])
        axis_2 = geomtypes.Vec3([1, 1, 0])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.D4D2(setup={"axis_n": axis_n, "axis_2": axis_2}),
            name="S4xI_D4D2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.transform_base(self.alt_base_pos)


class S4xI_D3C3(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 8 elements with final symmetry S4xI

        Special case of S4 X I / C3 where mu = 60 degrees. In this case two
        elements that share a 3-fold axis are mapped onto eachother
        """
        axis_n = geomtypes.Vec3([1, 1, 1])
        normal_r = geomtypes.Vec3([-1, 1, 0])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.D3C3(setup={"axis_n": axis_n, "normal_r": normal_r}),
            name="S4xI_D3C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )

        # the standard position isn't the right position
        base_rot = geomtypes.Rot3(axis=axis_n, angle=math.pi / 3)
        self.transform_base(base_rot)


class S4xI_D2C2(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 12 elements with final symmetry S4xI

        The descriptive shares 2 reflection planes through its 2-fold axis
        with 2 mirror planes through a 2-fold axis of the final symmetry.
        """
        axis_n = geomtypes.Vec3([1, 1, 0])
        normal_r = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.D2C2(setup={"axis_n": axis_n, "normal_r": normal_r}),
            name="S4xI_D2C2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )

        self.transform_base(self.alt_base_pos)
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 1, 0]), angle=math.pi / 4)
        self.transform_base(base_rot)


###############################################################################
#
# A5
#
###############################################################################
class A5_E(Compound):
    """General compound with A5 symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with A5 symmetry with central freedom."""
        super().__init__(
            base,
            isometry.A5(),
            isometry.E(),
            name="A5_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class A5_C3(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        -angle.ACOS_V2_3_V5_8,
        0,
        angle.ACOS_V10_4,
        angle.H_ACOS_1_3V5_8,
        angle.ACOS_1_3V5_8,
        angle.ACOS_7_3V5_3_2_2V5_8,
        angle.ACOS_7_3V5_16,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 20 elements with final symmetry A5 (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.A5(),
            isometry.C3(setup={"axis": axis}),
            name="A5_C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:3])


class A5_C2(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        math.pi / 4,
        angle.ATAN_V5_2,
        angle.ACOS_V5_1_2V3,
        angle.ATAN_1_V5,
        angle.TODO_26,
        angle.ACOS_V_5_V5_V10,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 30 elements with final symmetry A5 (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.A5(),
            isometry.C2(setup={"axis": axis}),
            name="A5_C2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


# Rigid Compounds
class A5_A4(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 5 elements with final symmetry A5

        With the orginisation as in the classical compound of 5 tetrahedra
        """
        super().__init__(
            base,
            isometry.A5(),
            isometry.A4(),
            name="A5_A4",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


###############################################################################
#
# A5 x I
#
###############################################################################
class A5xI_E(Compound):
    """General compound with A5xI symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with A5xI symmetry with central freedom."""
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.E(),
            name="A5xI_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class A5xI_C3(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        -angle.ACOS_V2_3_V5_8,
        0,
        angle.ACOS_V10_4,
        angle.H_ACOS_1_3V5_8,
        angle.ACOS_1_3V5_8,
        angle.ACOS_7_3V5_3_2_2V5_8,
        angle.ACOS_7_3V5_16,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 40 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.C3(setup={"axis": axis}),
            name="A5xI_C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:3])


class A5xI_C2(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        math.pi / 4,
        angle.ATAN_V5_2,
        angle.ACOS_V5_1_2V3,
        angle.ATAN_1_V5,
        angle.TODO_26,
        angle.ACOS_V_5_V5_V10,
        angle.ATAN_H_V2_1_V5_1,
        angle.TODO_41,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 60 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.C2(setup={"axis": axis}),
            name="A5xI_C2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


class A5xI_C2C1(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        3.55 * math.pi / 180,  # 6 * 10 | D15 x I / D3C3 ?
        # ~5
        20.91 * math.pi / 180,  # 10 * 12 | D12 x I / ? (col alt 2)
        # ~30.93 30 x 2 | ? , whereh 5 | .. is subcompound of 20 | A5 x I
        31.72 * math.pi / 180,  # 6 * 10 | D10 x I / ? # col alt 2) |
        33.83 * math.pi / 180,
        # ~37
        45.00 * math.pi / 180,  # 5 * 12 | S4 x I / D2C2
        58.26 * math.pi / 180,  # 6 * 10 | D20 x I / D4D2 ?
        66.98 * math.pi / 180,  # 6 * 10 | D15 x I / ? # col alt 2
        69.11 * math.pi / 180,  # 10 * 6 | D6 x I / ??
        75.64 * math.pi / 180,
    ]  # TODO calc algebraicly

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 60 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a reflection plane with the final symmetry
        """
        axis = geomtypes.Vec3([1, 0, 0])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.C2C1(setup={"axis": axis}),
            name="A5xI_C2C1",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )

        self.transform_base(self.alt_base_pos)
        self.set_rot_axis(axis, self.mu[:2])


# Rigid Compounds
class A5xI_A4(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 10 elements with final symmetry A5xI

        With the orginisation as in the classical compound of 10 tetrahedra
        """
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.A4(),
            name="A5xI_A4",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class A5xI_D3C3(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, version, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 20 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry and
        reflection planes fall together. The 'A' and 'B' versions occur in the
        same was as cube compound 10A and 10B occur.

        version: either 'A' or 'B'
        """
        versions = ["A", "B"]
        assert (
            version in versions
        ), f"{type(self).__name__} only supports versions {versions}"
        axis = geomtypes.Vec3([1, 1, 1])
        phi = (1 + V5) / 2
        normal = geomtypes.Vec3([-1, -phi, phi + 1])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.D3C3(setup={"axis_n": axis, "normal_r": normal}),
            name=f"{version}_A5xI_D3C3",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        if version == "A":
            mu = math.acos(V2 * V5 / 4)
        else:
            mu = -math.acos(V2 * (3 + V5) / 8)
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 1, 1]), angle=mu)
        self.transform_base(base_rot)


class A5xI_D2C2(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 30 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry and
        reflection planes fall together.
        """
        axis = geomtypes.Vec3([0, 0, 1])
        normal = geomtypes.Vec3([1, 0, 0])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.D2C2(setup={"axis_n": axis, "normal_r": normal}),
            name="A5xI_D2C2",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )

        self.transform_base(self.alt_base_pos)


###############################################################################
#
# Cn
#
###############################################################################
class Cn_E(Compound):
    """General compound with Cn symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, n, base, no_of_cols, col_alt=0, col_sym="", cols=None, n_fold_axis=None):
        """General compound with Cn symmetry with central freedom."""
        setup = {"n": n}
        if n_fold_axis:
            setup["axis"] = n_fold_axis
        super().__init__(
            base,
            isometry.Cn(setup=setup),
            isometry.E(),
            name=f"C{n}_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


###############################################################################
#
# C2nCn
#
###############################################################################
class C2nCn_E(Compound):
    """General compound with C2nCn symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, n, base, no_of_cols, col_alt=0, col_sym="", cols=None, n_fold_axis=None):
        """General compound with C2nCn symmetry with central freedom."""
        setup = {"n": n}
        if n_fold_axis:
            setup["axis"] = n_fold_axis
        elif n == 1:
            # C2C1 consists of {E, S} and the orientation of a 1-fold axis doesn't really matter. In
            # that case it makes more sense to have the reflection plane shared with the Z-axis.
            setup["axis"] = geomtypes.Vec3([1, 0, 0])
        super().__init__(
            base,
            isometry.C2nCn(setup=setup),
            isometry.E(),
            name=f"C{2 * n}C{n}_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


###############################################################################
#
# CnxI
#
###############################################################################
class CnxI_E(Compound):
    """General compound with CnxI symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, n, base, no_of_cols, col_alt=0, col_sym="", cols=None, n_fold_axis=None):
        """General compound with CnxI symmetry with central freedom."""
        setup = {"n": n}
        if n_fold_axis:
            setup["axis"] = n_fold_axis
        super().__init__(
            base,
            isometry.CnxI(setup=setup),
            isometry.E(),
            name=f"C{n}xI_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


###############################################################################
#
# DnCn
#
###############################################################################
class DnCn_E(Compound):
    """General compound with DnCn symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, n, base, no_of_cols, col_alt=0, col_sym="", cols=None, n_fold_axis=None):
        """General compound with DnCn symmetry with central freedom."""
        setup = {"n": n}
        if n_fold_axis:
            setup["axis"] = n_fold_axis
        super().__init__(
            base,
            isometry.DnCn(setup=setup),
            isometry.E(),
            name=f"D{n}C{n}_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


###############################################################################
#
# Dn
#
###############################################################################
class Dn_E(Compound):
    """General compound with Dn symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, n, base, no_of_cols, col_alt=0, col_sym="", cols=None, n_fold_axis=None):
        """General compound with Dn symmetry with central freedom."""
        setup = {"n": n}
        if n_fold_axis:
            setup["axis"] = n_fold_axis
        super().__init__(
            base,
            isometry.Dn(setup=setup),
            isometry.E(),
            name=f"D{n}_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


###############################################################################
#
# D2nDn
#
###############################################################################
class D2nDn_E(Compound):
    """General compound with D2nDn symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, n, base, no_of_cols, col_alt=0, col_sym="", cols=None, n_fold_axis=None):
        """General compound with D2nDn symmetry with central freedom."""
        setup = {"n": n}
        if n_fold_axis:
            setup["axis"] = n_fold_axis
        super().__init__(
            base,
            isometry.D2nDn(setup=setup),
            isometry.E(),
            name=f"D{2 * n}D{n}_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


###############################################################################
#
# DnxI
#
###############################################################################
class DnxI_E(Compound):
    """General compound with DnxI symmetry, the descriptive doesn't need to have any symmetry."""

    def __init__(self, n, base, no_of_cols, col_alt=0, col_sym="", cols=None, n_fold_axis=None):
        """General compound with DnxI symmetry with central freedom."""
        setup = {"n": n}
        if n_fold_axis:
            setup["axis"] = n_fold_axis
        super().__init__(
            base,
            isometry.DnxI(setup=setup),
            isometry.E(),
            name=f"D{n}xI_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
