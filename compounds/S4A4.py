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


if __name__ == "__main__":
    a4_c3 = A4_C3(tetrahedron, 4, col_alt=0)
    a4_c3.rot_base(math.pi/6)
    print(a4_c3.to_off())
