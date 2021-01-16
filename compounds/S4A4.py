#!env python
"""Classes to create compounds of polyhedra with tetrahedron symmetry.

All base elements should be positioned with the synnetries as the standard
tetrahedron below.
"""
from __future__ import print_function
import math

import geomtypes
import isometry
import orbit

V2 = math.sqrt(2)
V5 = math.sqrt(5)

tetrahedron = {
        'Vs': [
            geomtypes.Vec3([1, 1, 1]),
            geomtypes.Vec3([-1, -1, 1]),
            geomtypes.Vec3([1, -1, -1]),
            geomtypes.Vec3([-1, 1, -1])],
        'Fs': [
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 1],
            [1, 3, 2]]
}


class Compound(orbit.Shape):
    alt_base_pos = geomtypes.Rot3(axis=geomtypes.Vec3([0, 0, 1]),
                                  angle=math.pi/4)


###############################################################################
#
# A4
#
###############################################################################
class A4_E(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """General compound with A4 symmetry with central freedom."""
        super(A4_E, self).__init__(base,
                                   isometry.A4(),
                                   isometry.E(),
                                   name='A4_E',
                                   no_of_cols=no_of_cols, col_alt=col_alt,
                                   cols=cols,
                                   col_sym=col_sym)


class A4_C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 4 elements with final symmetry A4 (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(A4_C3, self).__init__(base,
                                    isometry.A4(),
                                    isometry.C3(setup={'axis': axis}),
                                    name='A4_C3',
                                    no_of_cols=no_of_cols, col_alt=col_alt,
                                    cols=cols,
                                    col_sym=col_sym)
        # Note double domain to show laevo and dextro
        self.set_rot_axis(axis, [-math.pi/3, math.pi/3])


###############################################################################
#
# A4 x I
#
###############################################################################
class A4xI_E(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """General compound with A4xI symmetry with central freedom."""
        super(A4xI_E, self).__init__(base,
                                     isometry.A4xI(),
                                     isometry.E(),
                                     name='A4xI_E',
                                     no_of_cols=no_of_cols, col_alt=col_alt,
                                     cols=cols,
                                     col_sym=col_sym)


class A4xI_C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 8 elements with final symmetry A4xI (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(A4xI_C3, self).__init__(base,
                                      isometry.A4xI(),
                                      isometry.C3(setup={'axis': axis}),
                                      name='A4xI_C3',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      cols=cols,
                                      col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/3])


class A4xI_C2C1(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 12 elements with final symmetry A4xI (rotation freedom)

        The descriptive shares a reflection plane with the final symmetry
        """
        axis = geomtypes.Vec3([1, 0, 0])
        super(A4xI_C2C1, self).__init__(base,
                                        isometry.A4xI(),
                                        isometry.C2C1(setup={'axis': axis}),
                                        name='A4xI_C2C1',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        self.transform_base(self.alt_base_pos)
        self.set_rot_axis(axis, [0, math.pi/4])


###############################################################################
#
# S4A4
#
###############################################################################
class S4A4_E(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """General compound with S4A4 symmetry with central freedom."""
        super(S4A4_E, self).__init__(base,
                                     isometry.S4A4(),
                                     isometry.E(),
                                     name='S4A4_E',
                                     no_of_cols=no_of_cols, col_alt=col_alt,
                                     cols=cols,
                                     col_sym=col_sym)


class S4A4_C4C2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 6 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a order 2 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super(S4A4_C4C2, self).__init__(base,
                                        isometry.S4A4(),
                                        isometry.C4C2(setup={'axis': axis}),
                                        name='S4A4_C4C2',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/4])


class S4A4_C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 8 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(S4A4_C3, self).__init__(base,
                                      isometry.S4A4(),
                                      isometry.C3(setup={'axis': axis}),
                                      name='S4A4_C3',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      cols=cols,
                                      col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/3])


class S4A4_C2C1(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 12 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a reflection plane with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super(S4A4_C2C1, self).__init__(base,
                                        isometry.S4A4(),
                                        isometry.C2C1(setup={'axis': axis}),
                                        name='S4A4_C2C1',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/2])


# Rigid Compounds
class S4A4_S4A4(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Trivial "compound" of 1 element with final symmetry S4A4

        The descriptive shares all symmetries with the final one.
        """
        super(S4A4_S4A4, self).__init__(base,
                                        isometry.S4A4(),
                                        isometry.S4A4(),
                                        name='S4A4_S4A4',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)


class S4A4_D3C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Rigid compound of 4 elements with S4A4 symmetry"""
        # Same as S4A4_C3 with special mu = 60 degrees
        axis = geomtypes.Vec3([1, 1, 1])
        normal = geomtypes.Vec3([-1, 1, 0])
        super(S4A4_D3C3, self).__init__(base,
                                        isometry.S4A4(),
                                        isometry.D3C3(setup={
                                            'axis_n': axis,
                                            'normal_r': normal}),
                                        name='S4A4_D3C3',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        # Move to rigid angle
        base_rot = geomtypes.Rot3(axis=axis, angle=math.pi/3)
        self.transform_base(base_rot)


###############################################################################
#
# S4
#
###############################################################################
class S4_E(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """General compound with S4 symmetry with central freedom."""
        super(S4_E, self).__init__(base,
                                   isometry.S4(),
                                   isometry.E(),
                                   name='S4_E',
                                   no_of_cols=no_of_cols, col_alt=col_alt,
                                   cols=cols,
                                   col_sym=col_sym)


class S4_C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 8 elements with final symmetry S4 (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(S4_C3, self).__init__(base,
                                    isometry.S4(),
                                    isometry.C3(setup={'axis': axis}),
                                    name='S4_C3',
                                    no_of_cols=no_of_cols, col_alt=col_alt,
                                    cols=cols,
                                    col_sym=col_sym)
        # Note double domain to show laevo and dextro
        self.set_rot_axis(axis, [-math.pi/3, math.pi/3])


class S4_C2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 12 elements with final symmetry S4 (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry (a pure
        2-fold axis, i.e. not a 4-fold axis)
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super(S4_C2, self).__init__(base,
                                    isometry.S4(),
                                    isometry.C2(setup={'axis': axis}),
                                    name='S4_C2',
                                    no_of_cols=no_of_cols, col_alt=col_alt,
                                    cols=cols,
                                    col_sym=col_sym)
        # Note double domain to show laevo and dextro
        self.set_rot_axis(axis, [-math.pi/4, math.pi/4])

        self.transform_base(self.alt_base_pos)


###############################################################################
#
# S4 x I
#
###############################################################################
class S4xI_E(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """General compound with S4xI symmetry with central freedom."""
        super(S4xI_E, self).__init__(base,
                                     isometry.S4xI(),
                                     isometry.E(),
                                     name='S4xI_E',
                                     no_of_cols=no_of_cols, col_alt=col_alt,
                                     cols=cols,
                                     col_sym=col_sym)


class S4xI_C4C2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 12 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 2-fold axis with the 4-fold axis in the final
        symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super(S4xI_C4C2, self).__init__(base,
                                        isometry.S4xI(),
                                        isometry.C4C2(setup={'axis': axis}),
                                        name='S4xI_C4C2',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/4])


class S4xI_C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 16 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(S4xI_C3, self).__init__(base,
                                      isometry.S4xI(),
                                      isometry.C3(setup={'axis': axis}),
                                      name='S4xI_C3',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      cols=cols,
                                      col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/3])


class S4xI_C2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 24 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry (a pure
        2-fold axis, i.e. not a 4-fold axis)
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super(S4xI_C2, self).__init__(base,
                                      isometry.S4xI(),
                                      isometry.C2(setup={'axis': axis}),
                                      name='S4xI_C2',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      cols=cols,
                                      col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/4])
        self.transform_base(self.alt_base_pos)


class S4xI_C2C1(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 24 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a reflection plane with one from the final
        symmetry in such a way that the normal of the reflection plane goes
        through a pure 2-fold axis of the final symmetry.
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super(S4xI_C2C1, self).__init__(base,
                                        isometry.S4xI(),
                                        isometry.C2C1(setup={'axis': axis}),
                                        name='S4xI_C2C1',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/2])


class S4xI_D1C1(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 24 elements with final symmetry S4xI (rotation freedom)

        The descriptive shares a reflection plane with one from the final
        symmetry in such a way that the normal of the reflection plane goes
        through a 4-fold axis of the final symmetry.
        """
        axis = geomtypes.Vec3([1, 0, 0])
        super(S4xI_D1C1, self).__init__(base,
                                        isometry.S4xI(),
                                        isometry.D1C1(setup={'axis': axis}),
                                        name='S4xI_D1C1',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.pi/4])

        self.transform_base(self.alt_base_pos)


# Rigid Compounds
class S4xI_S4A4(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Rigid ompound of 2 elements with final symmetry S4xI

        With the orginisation as the classical Stella Octangula.
        """
        super(S4xI_S4A4, self).__init__(base,
                                        isometry.S4xI(),
                                        isometry.S4A4(),
                                        name='S4xI_S4A4',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)


class S4xI_D4D2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Rigid ompound of 6 elements with final symmetry S4xI

        With the orginisation as the classical compound of 3 cubes, but by
        replacing each cube by a Stella Octangula.
        """
        axis_n = geomtypes.Vec3([0, 0, 1])
        axis_2 = geomtypes.Vec3([1, 1, 0])
        super(S4xI_D4D2, self).__init__(base,
                                        isometry.S4xI(),
                                        isometry.D4D2(setup={
                                            'axis_n': axis_n,
                                            'axis_2': axis_2}),
                                        name='S4xI_D4D2',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        self.transform_base(self.alt_base_pos)


class S4xI_D3C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Rigid ompound of 8 elements with final symmetry S4xI

        Special case of S4 X I / C3 where mu = 60 degrees. In this case two
        elements that share a 3-fold axis are mapped onto eachother
        """
        axis_n = geomtypes.Vec3([1, 1, 1])
        normal_r = geomtypes.Vec3([-1, 1, 0])
        super(S4xI_D3C3, self).__init__(base,
                                        isometry.S4xI(),
                                        isometry.D3C3(setup={
                                            'axis_n': axis_n,
                                            'normal_r': normal_r}),
                                        name='S4xI_D3C3',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)

        # the standard position isn't the right position
        base_rot = geomtypes.Rot3(axis=axis_n, angle=math.pi/3)
        self.transform_base(base_rot)


class S4xI_D2C2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Rigid ompound of 12 elements with final symmetry S4xI

        The descriptive shares 2 reflection planes through its 2-fold axis
        with 2 mirror planes through a 2-fold axis of the final symmetry.
        """
        axis_n = geomtypes.Vec3([1, 1, 0])
        normal_r = geomtypes.Vec3([0, 0, 1])
        super(S4xI_D2C2, self).__init__(base,
                                        isometry.S4xI(),
                                        isometry.D2C2(setup={
                                            'axis_n': axis_n,
                                            'normal_r': normal_r}),
                                        name='S4xI_D2C2',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)

        self.transform_base(self.alt_base_pos)
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 1, 0]),
                                  angle=math.pi/4)
        self.transform_base(base_rot)


###############################################################################
#
# A5
#
###############################################################################
class A5_E(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """General compound with A5 symmetry with central freedom."""
        super(A5_E, self).__init__(base,
                                   isometry.A5(),
                                   isometry.E(),
                                   name='A5_E',
                                   no_of_cols=no_of_cols, col_alt=col_alt,
                                   cols=cols,
                                   col_sym=col_sym)


class A5_C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 20 elements with final symmetry A5 (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(A5_C3, self).__init__(base,
                                    isometry.A5(),
                                    isometry.C3(setup={'axis': axis}),
                                    name='A5_C3',
                                    no_of_cols=no_of_cols, col_alt=col_alt,
                                    cols=cols,
                                    col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.acos(V2 * V5 / 4)])


class A5_C2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 30 elements with final symmetry A5 (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super(A5_C2, self).__init__(base,
                                    isometry.A5(),
                                    isometry.C2(setup={'axis': axis}),
                                    name='A5_C2',
                                    no_of_cols=no_of_cols, col_alt=col_alt,
                                    cols=cols,
                                    col_sym=col_sym)
        self.set_rot_axis(axis)


# Rigid Compounds
class A5_A4(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Rigid ompound of 5 elements with final symmetry A5

        With the orginisation as in the classical compound of 5 tetrahedra
        """
        super(A5_A4, self).__init__(base,
                                    isometry.A5(),
                                    isometry.A4(),
                                    name='A5_A4',
                                    no_of_cols=no_of_cols, col_alt=col_alt,
                                    cols=cols,
                                    col_sym=col_sym)


###############################################################################
#
# A5 x I
#
###############################################################################
class A5xI_E(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """General compound with A5xI symmetry with central freedom."""
        super(A5xI_E, self).__init__(base,
                                     isometry.A5xI(),
                                     isometry.E(),
                                     name='A5xI_E',
                                     no_of_cols=no_of_cols, col_alt=col_alt,
                                     cols=cols,
                                     col_sym=col_sym)


class A5xI_C3(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 40 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(A5xI_C3, self).__init__(base,
                                      isometry.A5xI(),
                                      isometry.C3(setup={'axis': axis}),
                                      name='A5xI_C3',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      cols=cols,
                                      col_sym=col_sym)
        self.set_rot_axis(axis, [0, math.acos(V2 * V5 / 4)])


class A5xI_C2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 60 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super(A5xI_C2, self).__init__(base,
                                      isometry.A5xI(),
                                      isometry.C2(setup={'axis': axis}),
                                      name='A5xI_C2',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      cols=cols,
                                      col_sym=col_sym)
        self.set_rot_axis(axis)


class A5xI_C2C1(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 60 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a reflection plane with the final symmetry
        """
        axis = geomtypes.Vec3([1, 0, 0])
        super(A5xI_C2C1, self).__init__(base,
                                        isometry.A5xI(),
                                        isometry.C2C1(setup={'axis': axis}),
                                        name='A5xI_C2C1',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)

        self.transform_base(self.alt_base_pos)
        self.set_rot_axis(axis)


# Rigid Compounds
class A5xI_A4(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Rigid ompound of 10 elements with final symmetry A5xI

        With the orginisation as in the classical compound of 10 tetrahedra
        """
        super(A5xI_A4, self).__init__(base,
                                      isometry.A5xI(),
                                      isometry.A4(),
                                      name='A5xI_A4',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      cols=cols,
                                      col_sym=col_sym)


class A5xI_D3C3(Compound):
    def __init__(self, version, base, no_of_cols, col_alt=0, col_sym='',
                 cols=None):
        """Compound of 20 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry and
        reflection planes fall together. The 'A' and 'B' versions occur in the
        same was as cube compound 10A and 10B occur.

        version: either 'A' or 'B'
        """
        axis = geomtypes.Vec3([1, 1, 1])
        phi = (1 + V5) / 2
        normal = geomtypes.Vec3([-1, -phi, phi + 1])
        super(A5xI_D3C3, self).__init__(base,
                                        isometry.A5xI(),
                                        isometry.D3C3(setup={
                                            'axis_n': axis,
                                            'normal_r': normal}),
                                        name='{}_A5xI_D3C3'.format(version),
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)
        if version == 'A':
            mu = math.acos(V2 * V5 / 4)
        else:
            mu = -math.acos(V2 * (3 + V5) / 8)
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 1, 1]),
                                  angle=mu)
        self.transform_base(base_rot)


class A5xI_D2C2(Compound):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym='', cols=None):
        """Compound of 30 elements with final symmetry A5xI (rotation freedom)

        The descriptive shares a 2-fold axis with the final symmetry and
        reflection planes fall together.
        """
        axis = geomtypes.Vec3([0, 0, 1])
        normal = geomtypes.Vec3([1, 0, 0])
        super(A5xI_D2C2, self).__init__(base,
                                        isometry.A5xI(),
                                        isometry.D2C2(setup={
                                            'axis_n': axis,
                                            'normal_r': normal}),
                                        name='A5xI_D2C2',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        cols=cols,
                                        col_sym=col_sym)

        self.transform_base(self.alt_base_pos)


if __name__ == "__main__":
    a4_c3 = A4_C3(tetrahedron, 4, col_alt=0)
    a4_c3.rot_base(math.pi/6)
    print(a4_c3.to_off())
