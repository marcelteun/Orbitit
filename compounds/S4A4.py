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


###############################################################################
#
# A4
#
###############################################################################
class A4_E(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """General compound with A4 symmetry with central freedom."""
        super(A4_E, self).__init__(base,
                                   isometry.A4(),
                                   isometry.E(),
                                   name='A4_E',
                                   no_of_cols=no_of_cols, col_alt=col_alt,
                                   col_sym=col_sym)


class A4_C3(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """Compound of 4 elements with final symmetry A4 (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(A4_C3, self).__init__(base,
                                    isometry.A4(),
                                    isometry.C3(setup={'axis': axis}),
                                    name='A4_C3',
                                    no_of_cols=no_of_cols, col_alt=col_alt,
                                    col_sym=col_sym)
        self.set_rot_axis(axis)


###############################################################################
#
# A4 x I
#
###############################################################################
class A4xI_E(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """General compound with A4xI symmetry with central freedom."""
        super(A4xI_E, self).__init__(base,
                                     isometry.A4xI(),
                                     isometry.E(),
                                     name='A4xI_E',
                                     no_of_cols=no_of_cols, col_alt=col_alt,
                                     col_sym=col_sym)


class A4xI_C3(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """Compound of 8 elements with final symmetry A4xI (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(A4xI_C3, self).__init__(base,
                                      isometry.A4xI(),
                                      isometry.C3(setup={'axis': axis}),
                                      name='A4xI_C3',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      col_sym=col_sym)
        self.set_rot_axis(axis)


class A4xI_C2C1(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """Compound of 12 elements with final symmetry A4xI (rotation freedom)

        The descriptive shares a reflection plane with the final symmetry
        """
        axis = geomtypes.Vec3([1, 0, 0])
        super(A4xI_C2C1, self).__init__(base,
                                        isometry.A4xI(),
                                        isometry.C2C1(setup={'axis': axis}),
                                        name='A4xI_C2C1',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        col_sym=col_sym)
        # the standard position isn't the right position
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([0, 0, 1]),
                                  angle=math.pi/4)
        self.transform_base(base_rot)
        self.set_rot_axis(axis)


###############################################################################
#
# S4A4
#
###############################################################################
class S4A4_E(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """General compound with S4A4 symmetry with central freedom."""
        super(S4A4_E, self).__init__(base,
                                     isometry.S4A4(),
                                     isometry.E(),
                                     name='S4A4_E',
                                     no_of_cols=no_of_cols, col_alt=col_alt,
                                     col_sym=col_sym)


class S4A4_C4C2(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """Compound of 6 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a order 2 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([0, 0, 1])
        super(S4A4_C4C2, self).__init__(base,
                                        isometry.S4A4(),
                                        isometry.C4C2(setup={'axis': axis}),
                                        name='S4A4_C4C2',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        col_sym=col_sym)
        self.set_rot_axis(axis)


class S4A4_C3(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """Compound of 8 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a order 3 symmetry axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(S4A4_C3, self).__init__(base,
                                      isometry.S4A4(),
                                      isometry.C3(setup={'axis': axis}),
                                      name='S4A4_C3',
                                      no_of_cols=no_of_cols, col_alt=col_alt,
                                      col_sym=col_sym)
        self.set_rot_axis(axis)


class S4A4_C2C1(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """Compound of 12 elements with final symmetry S4A4 (rotation freedom)

        The descriptive shares a reflection plane with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 0])
        super(S4A4_C2C1, self).__init__(base,
                                        isometry.S4A4(),
                                        isometry.C2C1(setup={'axis': axis}),
                                        name='S4A4_C2C1',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        col_sym=col_sym)
        self.set_rot_axis(axis)


# Rigid Compounds
class S4A4_S4A4(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """Trivial "compound" of 1 element with final symmetry S4A4

        The descriptive shares all symmetries with the final one.
        """
        super(S4A4_S4A4, self).__init__(base,
                                        isometry.S4A4(),
                                        isometry.S4A4(),
                                        name='S4A4_S4A4',
                                        no_of_cols=no_of_cols, col_alt=col_alt,
                                        col_sym=col_sym)


class S4A4_D3C3(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
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
                                        col_sym=col_sym)
        # Move to rigid angle
        base_rot = geomtypes.Rot3(axis=axis, angle=math.pi/3)
        self.transform_base(base_rot)


###############################################################################
#
# S4
#
###############################################################################
class S4_E(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """General compound with S4 symmetry with central freedom."""
        super(S4_E, self).__init__(base,
                                   isometry.S4(),
                                   isometry.E(),
                                   name='S4_E',
                                   no_of_cols=no_of_cols, col_alt=col_alt,
                                   col_sym=col_sym)


class S4_C3(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
        """Compound of 8 elements with final symmetry S4 (rotation freedom)

        The descriptive shares a 3-fold axis with the final symmetry
        """
        axis = geomtypes.Vec3([1, 1, 1])
        super(S4_C3, self).__init__(base,
                                    isometry.S4(),
                                    isometry.C3(setup={'axis': axis}),
                                    name='S4_C3',
                                    no_of_cols=no_of_cols, col_alt=col_alt,
                                    col_sym=col_sym)
        self.set_rot_axis(axis)


class S4_C2(orbit.Shape):
    def __init__(self, base, no_of_cols, col_alt=0, col_sym=''):
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
                                    col_sym=col_sym)
        self.set_rot_axis(axis)

        # the standard position isn't the right position
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([0, 0, 1]),
                                  angle=math.pi/4)
        self.transform_base(base_rot)


if __name__ == "__main__":
    a4_c3 = A4_C3(tetrahedron, 4, col_alt=0)
    a4_c3.rot_base(math.pi/6)
    print(a4_c3.to_off())
