#!/usr/bin/env python
"""Classes to create compounds of polyhedra with tetrahedron symmetry.

All base elements should be positioned with the synnetries as the standard
tetrahedron below.
"""

import math

from orbitit.compounds import base
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
    base_to_o2 = geomtypes.Rot3(axis=geomtypes.Vec3([1, 0, 0]), angle=math.pi / 4)


###############################################################################
#
# A4 x I
#
###############################################################################
class A4xI_ExI(Compound):
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

    mu = [0, math.pi / 2, base.ASIN_1_V3]

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

    mu = [0, math.pi / 3, base.D_ATAN_V3_2_V5]

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

    mu = [0, base.ASIN_2V2_3, math.pi / 2, base.ASIN_1_V3, base.ACOS_1_V3, math.pi / 4]

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

    mu = [
        0,
        math.pi / 4,
        base.ACOS_1_V3 - math.pi / 4,
        base.ASIN_1_V3,
        math.pi / 8,
        base.ATAN_4V2_7 / 2,
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

    mu = [
        0,
        math.pi / 4,
        base.ACOS_1_V3 - math.pi / 4,
        base.ASIN_1_V3,
        math.pi / 8,
        base.ATAN_4V2_7 / 2,
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

    mu = [0, math.pi / 3, base.D_ATAN_V3_2_V5, math.pi / 6]

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
