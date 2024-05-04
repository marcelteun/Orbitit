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

from orbitit.compounds import angle
from orbitit import geomtypes, isometry, orbit


cube = {
    "vs": [
        geomtypes.Vec3([1, 1, -1]),
        geomtypes.Vec3([1, -1, -1]),
        geomtypes.Vec3([-1, -1, -1]),
        geomtypes.Vec3([-1, 1, -1]),
        geomtypes.Vec3([1, 1, 1]),
        geomtypes.Vec3([-1, 1, 1]),
        geomtypes.Vec3([-1, -1, 1]),
        geomtypes.Vec3([1, -1, 1]),
    ],
    "fs": [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [4, 7, 1, 0],
        [5, 4, 0, 3],
        [6, 5, 3, 2],
        [7, 6, 2, 1],
    ],
}


class Compound(orbit.Shape):
    """A compound object, see orbit.Shape class for more info."""

    base_to_o2 = geomtypes.Rot3(axis=geomtypes.Vec3([1, 0, 0]), angle=math.pi / 4)


###############################################################################
#
# A4 x I
#
###############################################################################
class A4xI_ExI(Compound):
    """General compound with spherical freedom, see __init__ for more info."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with A4xI symmetry with central freedom."""
        super().__init__(
            base,
            isometry.A4xI(),
            isometry.ExI(),
            name="A4xI_ExI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class A4xI_C2xI(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 2, angle.ASIN_1_V3]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 6 elements with final symmetry A4xI (rotation freedom)

        The descriptive shares an order 2 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.A4xI(),
            isometry.C2xI(setup={"axis": axis}),
            name="A4xI_C2xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.transform_base(self.base_to_o2)
        self.set_rot_axis(axis, self.mu[:2])


class A4xI_C3xI(Compound):
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
            isometry.C3xI(setup={"axis": axis}),
            name="A4xI_C3xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


###############################################################################
#
# S4 x I
#
###############################################################################
class S4xI_ExI(Compound):
    """General compound with spherical freedom, see __init__ for more info."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound with S4xI symmetry with central freedom."""
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.ExI(),
            name="S4xI_E",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class S4xI_C2xI_A(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        angle.ASIN_2V2_3,
        math.pi / 2,
        angle.ASIN_1_V3,
        angle.ACOS_1_V3,
        math.pi / 4,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 12 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 2-fold axis with the 2-fold axis in the final
        symmetry
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C2xI(setup={"axis": axis}),
            name="A_S4xI_C2xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:3])


class S4xI_C2xI_B(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        math.pi / 4,
        angle.ACOS_1_V3 - math.pi / 4,
        angle.ASIN_1_V3,
        math.pi / 8,
        angle.ATAN_4V2_7 / 2,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 12 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 4-fold axis with the 2-fold axis in the final
        symmetry
        """
        axis = geomtypes.Vec3([0, 1, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C2xI(setup={"axis": axis}),
            name="B_S4xI_C2xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])
        self.transform_base(self.base_to_o2)


class S4xI_D1xI(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        math.pi / 4,
        angle.ACOS_1_V3 - math.pi / 4,
        angle.ASIN_1_V3,
        math.pi / 8,
        angle.ATAN_4V2_7 / 2,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 12 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 2-fold axis with the 4-fold axis in the final
        symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C2xI(setup={"axis": axis}),
            name="S4xI_D1xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, [self.mu[0], self.mu[1]])
        self.transform_base(self.base_to_o2)


class S4xI_C3xI(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 3, angle.D_ATAN_V3_2_V5, math.pi / 6]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 8 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C3xI(setup={"axis": axis}),
            name="S4xI_C3xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, [self.mu[0], self.mu[1]])


class S4xI_C4xI(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [0, math.pi / 4, math.pi / 8]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 6 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 4-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.C4xI(setup={"axis": axis}),
            name="S4xI_C4xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, [self.mu[0], self.mu[1]])


# Rigid Compounds
class S4xI_S4xI(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 1 elements with final symmetry S4xI"""
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.S4xI(),
            name="S4xI_S4A4",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class S4xI_D4xI(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 3 elements with final symmetry S4xI

        For a cube this is the classical compound of three cubes.
        """
        axis_n = geomtypes.Vec3([1, 0, 0])
        axis_2 = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.D4xI(setup={"axis_n": axis_n, "axis_2": axis_2}),
            name="S4xI_D4xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.transform_base(self.base_to_o2)


class S4xI_D3xI(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 4 elements with final symmetry S4xI

        For a cube this gives Bakos' compound.
        """
        axis_n = geomtypes.Vec3([1, 1, 1])
        axis_2 = geomtypes.Vec3([0, -1, 1])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.D3xI(setup={"axis_n": axis_n, "axis_2": axis_2}),
            name="S4xI_D3xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )

        # the standard position isn't the right position
        base_rot = geomtypes.Rot3(axis=axis_n, angle=math.pi / 3)
        self.transform_base(base_rot)


class S4xI_D2xI(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 6 elements with final symmetry S4xI

        The descriptive shares a 2-fold axis with two orthogonal reflection planes (meeting the in
        the 2-fold axis) with a 4-fold axis of S4xI, including the reflection planes.
        """
        axis_n = geomtypes.Vec3([0, 0, 1])
        axis_2 = geomtypes.Vec3([1, 1, 0])
        super().__init__(
            base,
            isometry.S4xI(),
            isometry.D2xI(setup={"axis_n": axis_n, "axis_2": axis_2}),
            name="S4xI_D2xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )

        self.transform_base(self.base_to_o2)
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([0, 0, 1]), angle=math.pi / 4)
        self.transform_base(base_rot)


###############################################################################
#
# A5 x I
#
###############################################################################
class A5xI_ExI(Compound):
    """General compound with spherical freedom, see __init__ for more info."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """General compound of 60 with A5xI symmetry with central freedom."""
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.ExI(),
            name="A5xI_ExI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class A5xI_C2xI_A(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        angle.ATAN_H_V2_1_V5__1,
        angle.ACOS_V2_1_V5_V2_1__6,
        math.pi / 2,
        angle.ASIN_1_V3,  # 4
        angle.ACOS_1_V3,
        angle.ACOS_V5_1_2V3,  # 6
        angle.ACOS_V_5_V5_V10,
        angle.ASIN_V_5_V5_V10,  # 8
        angle.ASIN_V5_1_2V3,
        math.pi / 4,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 30 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.C2xI(setup={"axis": axis}),
            name="A_A5xI_C2xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:4])
        self.transform_base(self.base_to_o2)


class A5xI_C2xI_B(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        0,
        math.pi / 4,
        angle.ATAN_V5_2,
        angle.ACOS_V5_1_2V3,  # 3
        angle.ATAN_1_V5,
        angle.ACOS_V_5_V5_V10,  # 5
        math.pi / 8,
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 30 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 4-fold axis with a 2-fold axis in the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.C2xI(setup={"axis": axis}),
            name="B_A5xI_C2xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:2])


class A5xI_C3xI(Compound):
    """Compound with rotational freedom axis, see __init__ for more."""

    mu = [
        -angle.ACOS_V2_3_V5_8,
        0,
        angle.ACOS_V10_4,  # 2
        angle.ACOS_7_3V5_16,
        angle.ACOS_7_3V5_3_2_2V5_8,  # 4
        angle.ACOS_1_3V5_8,
        angle.H_ACOS_1_3V5_8,  # 6
    ]

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 20 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.C3xI(setup={"axis": axis}),
            name="A5xI_C3xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        self.set_rot_axis(axis, self.mu[:3])


# Rigid Compounds
class A5xI_A4xI(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Rigid ompound of 5 elements with final symmetry A5xI

        With the orginisation as in the classical compound of 5 cubes
        """
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.A4xI(),
            name="A5xI_A4",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )


class A5xI_D3xI(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, version, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 10 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry and three
        reflection planes that meet in that same axis.

        version: either 'A' or 'B'
        """
        axis = geomtypes.Vec3([1, 1, 1])
        axis_2 = geomtypes.Vec3([1, 0, 0])
        phi = (1 + angle.V5) / 2
        axis_2 = geomtypes.Vec3([-1, -phi, phi + 1])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.D3xI(setup={"axis_n": axis, "axis_2": axis_2}),
            name="{}_A5xI_D3xI".format(version),
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )
        mu_i = 2 if version == "A" else 0
        base_rot = geomtypes.Rot3(axis=axis, angle=A5xI_C3xI.mu[mu_i])
        self.transform_base(base_rot)


class A5xI_D2xI(Compound):
    """Rigid compound, see __init__ for more."""

    def __init__(self, base, no_of_cols, col_alt=0, col_sym="", cols=None):
        """Compound of 15 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry and
        reflection planes fall together.
        """
        axis = geomtypes.Vec3([0, 0, 1])
        axis_2 = geomtypes.Vec3([1, 0, 0])
        super().__init__(
            base,
            isometry.A5xI(),
            isometry.D2xI(setup={"axis_n": axis, "axis_2": axis_2}),
            name="A5xI_D2xI",
            no_of_cols=no_of_cols,
            col_alt=col_alt,
            cols=cols,
            col_sym=col_sym,
        )

        self.transform_base(self.base_to_o2)
