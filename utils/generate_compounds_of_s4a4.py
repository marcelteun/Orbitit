#!/usr/bin/env python
"""
Generate off-files for compound polyhedra of polyhedra with tetrahedral symmetra.
"""

# pylint: disable=too-many-statements

import argparse
import math
import os

from orbitit.compounds import S4A4
from orbitit import geomtypes, rgb

# TODO: check if col_alt with Python3 still gives the same alternatives
V2 = math.sqrt(2)
V3 = math.sqrt(3)
V5 = math.sqrt(5)
V10 = math.sqrt(10)
# ~13.283 degrees:
ATAN_V5_2 = math.atan(V5 - 2)
# ~44.4775 degrees:
ACOS__1_3V5_8 = math.acos((-1 + 3 * V5) / 8)
# 20.905
ACOS_V5_1_2V3 = math.acos((V5 + 1) / (2 * V3))
# ~23.4309
ACOS_7_3V5_3_2_2V5_8 = math.acos((-7 + 3*V5 + 3*math.sqrt(2 + 2*V5)) / 8)
# ~24.09
ATAN_1_V5 = math.atan(1 / V5)
# ~31.0449 degrees:
acos_7_3V5_16 = math.acos((7 + 3*V5) / 16)
# ~31.7175 degrees
ACOS_V_5_V5_V10 = math.acos(math.sqrt(5 + V5) / V10)
# ~35.2644 degrees:
ASIN_1_V3 = math.asin(1 / V3)
# ~54.7356 degrees:
ACOS_1_V3 = math.acos(1 / V3)

# ~38.9424 degrees:
ATAN_4V2_7 = math.atan(4 * V2 / 7)
# ~44.4775 degrees:
D_ATAN_V3_2_V5 = -2 * math.atan(V3 * (2 - V5))
# ~9.7356 degrees:
ATAN_3_2V2 = math.atan(3 - 2 * V2)
# ~33.8305 degrees:
ATAN_H_V2_1_V5_1 = math.atan((V2 - 1) * (1 + V5) / 2)
# ~14.3592 degrees:
ATAN_H_V2_1_V5__1 = math.atan((V2 - 1) * (V5 - 1) / 2)
# ~19.4712 degrees:
ATAN_V2_4 = math.atan(V2 / 4)

# ~15.5225 degrees:
ACOS_1_3V5_8 = math.acos((1+3*V5) / 8)
# ~7.7612 degrees:
H_ACOS_1_3V5_8 = ACOS_1_3V5_8 / 2

def save_off(comp, tail=''):
    """Save compound polyhedron in the OFF format.

    The filename will state the amount of elements and then use the compounds internal name.
    comp: the orbit.Shape object of the compound. From this the name and amount of constituents is
        used for the file name
    tail: this will be added to the end of the file name. Typically this is used to add the special
        angle in the case of a compound with rotational freedom.
    """
    # If this starts with a version then we need 2A_, 2B etc (not 2_A_)
    sep = '_' if comp.name[1] != '_' else ''
    with open(f'{comp.index}{sep}{comp.name}{tail}.off', 'w') as fd:
        fd.write(comp.to_off())


def create_a4(base, js_fd=None):
    """Create all compounds with the rotational symmetry of a tetrahedron."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]),
                              angle=math.pi/4)
    polyh = S4A4.A4_E(base, 4, col_alt=1)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4A4.A4_C3(base, 4)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    # example angle for which the compound is 5 | A5 / A4 with 1 removed
    polyh.rot_base(D_ATAN_V3_2_V5)
    save_off(polyh)


def create_a4xi(base, js_fd=None):
    """Create all compounds with the rotational symmetry of a tetrahedron and a cetral inversion."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]),
                              angle=math.pi/6)
    polyh = S4A4.A4xI_E(base, 4, col_alt=2)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4A4.A4xI_C3(base, 4)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(5*math.pi/18)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.A4xI_C3(base, 4, cols=[S4A4.A4xI_C3.cols[0],
                                        S4A4.A4xI_C3.cols[1],
                                        S4A4.A4xI_C3.cols[1],
                                        S4A4.A4xI_C3.cols[0]])
    polyh.rot_base(D_ATAN_V3_2_V5)
    save_off(polyh, '_mu2')

    polyh = S4A4.A4xI_C2C1(base, 3)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/6)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.A4xI_C2C1(base, 3)
    polyh.rot_base(ASIN_1_V3)
    save_off(polyh, '_mu2')


def create_s4a4(base, js_fd=None):
    """Create all compounds with the complete symmetry of a tetrahedron."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]),
                              angle=math.pi/4)
    polyh = S4A4.S4A4_E(base, 4, col_alt=0)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4A4.S4A4_C4C2(base, 3)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/6)  # example angle
    save_off(polyh)

    polyh = S4A4.S4A4_C3(base, 4)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/5)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4A4_C3(base, 4)
    polyh.rot_base(math.pi/6)
    save_off(polyh, '_mu2')

    polyh = S4A4.S4A4_C2C1(base, 3)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/6)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4A4_C2C1(base, 3)
    polyh.rot_base(ACOS_1_V3)
    save_off(polyh, '_mu3')

    # Rigid compounds
    polyh = S4A4.S4A4_S4A4(base, 1)
    save_off(polyh)

    polyh = S4A4.S4A4_D3C3(base, 4)
    save_off(polyh)


def create_s4(base, js_fd=None):
    """Create all compounds with the rotational symmetry of a cube."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 1]),
                              angle=2*math.pi/9)
    polyh = S4A4.S4_E(base, 6, col_alt=2, col_sym='C4')
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4A4.S4_C3(base, 4)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(D_ATAN_V3_2_V5)  # use special angle as example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4_C3(base, 4)
    polyh.rot_base(math.pi/6)
    save_off(polyh, '_mu2')
    polyh = S4A4.S4_C3(base, 4)
    polyh = S4A4.S4_C3(base, 8,
                       cols=[S4A4.S4_C3.cols[0],
                             S4A4.S4_C3.cols[0],
                             S4A4.S4_C3.cols[1],
                             S4A4.S4_C3.cols[1],
                             S4A4.S4_C3.cols[2],
                             S4A4.S4_C3.cols[2],
                             S4A4.S4_C3.cols[3],
                             S4A4.S4_C3.cols[3]])
    polyh.rot_base(D_ATAN_V3_2_V5)
    save_off(polyh, '_mu3')

    polyh = S4A4.S4_C2(base, 6)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(27.968 * math.pi / 180)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4_C2(base, 4, col_alt=1)
    polyh.rot_base(ATAN_3_2V2)
    save_off(polyh, '_mu2')
    polyh = S4A4.S4_C2(base, 4)
    polyh.rot_base(ASIN_1_V3)
    save_off(polyh, '_mu3')
    polyh = S4A4.S4_C2(base, 12,
                       cols=[S4A4.S4_C2.cols[0],
                             S4A4.S4_C2.cols[1],
                             rgb.gray,
                             rgb.gray,
                             rgb.gray,
                             S4A4.S4_C2.cols[1],
                             S4A4.S4_C2.cols[3],
                             S4A4.S4_C2.cols[2],
                             S4A4.S4_C2.cols[3],
                             S4A4.S4_C2.cols[0],
                             rgb.gray,
                             S4A4.S4_C2.cols[2],
                            ],
                       )
    polyh.rot_base(2*ATAN_3_2V2)
    save_off(polyh, '_mu4')
    polyh = S4A4.S4_C2(base, 12,
                       cols=[S4A4.S4_C2.cols[0],
                             S4A4.S4_C2.cols[0],
                             rgb.gray,
                             rgb.gray,
                             rgb.gray,
                             S4A4.S4_C2.cols[3],
                             S4A4.S4_C2.cols[2],
                             S4A4.S4_C2.cols[1],
                             S4A4.S4_C2.cols[3],
                             S4A4.S4_C2.cols[1],
                             rgb.gray,
                             S4A4.S4_C2.cols[2],
                            ],
                       )
    polyh.rot_base(ATAN_H_V2_1_V5__1)
    save_off(polyh, '_mu5')
    polyh = S4A4.S4_C2(base, 12,
                       cols=[rgb.gray,
                             S4A4.S4_C2.cols[1],
                             S4A4.S4_C2.cols[2],
                             S4A4.S4_C2.cols[1],
                             S4A4.S4_C2.cols[3],
                             rgb.gray,
                             rgb.gray,
                             rgb.gray,
                             S4A4.S4_C2.cols[3],
                             S4A4.S4_C2.cols[0],
                             S4A4.S4_C2.cols[0],
                             S4A4.S4_C2.cols[2],
                            ],
                       )
    polyh.rot_base(ATAN_H_V2_1_V5_1)
    save_off(polyh, '_mu6')


def create_s4xi(base, js_fd=None):
    """Create all compounds with the complete symmetry of a cube."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([2, 1, 0]),
                              angle=math.pi/2)
    polyh = S4A4.S4xI_E(base, 6, col_sym='C4xI')
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4A4.S4xI_C4C2(base, 6, col_sym='C4xI')
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/3)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4xI_C4C2(base, 3)
    polyh.rot_base(math.pi / 8)
    save_off(polyh, '_mu2')

    polyh = S4A4.S4xI_C3(base, 4, col_sym='D3xI')
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(2*math.pi/9)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4xI_C3(base, 4, col_sym='D3xI')
    polyh.rot_base(math.pi / 6)
    save_off(polyh, '_mu2')
    polyh = S4A4.S4xI_C3(base, 2, col_sym='S4')
    polyh.rot_base(D_ATAN_V3_2_V5)
    save_off(polyh, '_mu3')
    polyh = S4A4.S4xI_C3(base, 2, col_sym='A4xI')
    polyh.rot_base(D_ATAN_V3_2_V5)
    save_off(polyh, '_mu3_1')

    polyh = S4A4.S4xI_C2(base, 6, col_sym='D2xI')
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/9)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4xI_C2(base, 4, col_alt=1)
    polyh.rot_base(ACOS_1_V3 - math.pi / 4)
    save_off(polyh, '_mu2')
    polyh = S4A4.S4xI_C2(base, 4, col_alt=0)
    polyh.rot_base(ASIN_1_V3)
    save_off(polyh, '_mu3')
    polyh = S4A4.S4xI_C2(base, 6, col_sym='D2xI')
    polyh.rot_base(math.pi / 8)
    save_off(polyh, '_mu4')
    polyh = S4A4.S4xI_C2(base, 12, col_sym='C2xI',
                         cols=[S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[0],
                               ])
    polyh.rot_base(ATAN_4V2_7 / 2)
    save_off(polyh, '_mu5')
    # FIXME: generated in a different order after upgrading Python
    polyh = S4A4.S4xI_C2(base, 24, col_sym='C2xI',
                         cols=[S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[3]])
    polyh.rot_base(ATAN_H_V2_1_V5__1)
    save_off(polyh, '_mu6')
    # FIXME: generated in a different order after upgrading Python
    polyh = S4A4.S4xI_C2(base, 24, col_sym='C2xI',
                         cols=[S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[1]])
    polyh.rot_base(ATAN_H_V2_1_V5_1)
    save_off(polyh, '_mu7')

    polyh = S4A4.S4xI_C2C1(base, 6, col_sym='D4C4')
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(2*math.pi/9)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4xI_C2C1(base, 6, col_sym='D2xI')
    polyh.rot_base(ASIN_1_V3)
    save_off(polyh, '_mu3')
    polyh = S4A4.S4xI_C2C1(base, 3)
    polyh.rot_base(ACOS_1_V3)
    save_off(polyh, '_mu4')
    polyh = S4A4.S4xI_C2C1(base, 6, col_sym='D2xI')
    polyh.rot_base(math.pi/4)
    save_off(polyh, '_mu5')

    polyh = S4A4.S4xI_D1C1(base, 6, col_sym='D4C4')
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(16 * math.pi / 180)  # example angle
    save_off(polyh)
    # special mu
    #            , , , math.pi/8, ACOS_1_V3]
    polyh = S4A4.S4xI_D1C1(base, 12, col_sym='D2C2', col_alt=2)
    polyh.rot_base(ATAN_V2_4/2)
    save_off(polyh, '_mu2')
    polyh = S4A4.S4xI_D1C1(base, 3, col_alt=1)
    polyh.rot_base(ATAN_V2_4)
    save_off(polyh, '_mu3')
    polyh = S4A4.S4xI_D1C1(base, 3)
    polyh.rot_base(math.pi/8)
    save_off(polyh, '_mu4')
    polyh = S4A4.S4xI_D1C1(base, 3, col_alt=1)
    polyh.rot_base(ASIN_1_V3)
    save_off(polyh, '_mu5')

    # Rigid compounds
    polyh = S4A4.S4xI_S4A4(base, 2)
    save_off(polyh)

    polyh = S4A4.S4xI_D4D2(base, 3)
    save_off(polyh)

    polyh = S4A4.S4xI_D3C3(base, 4)
    save_off(polyh)

    polyh = S4A4.S4xI_D2C2(base, 3)
    save_off(polyh)


def create_a5(base, js_fd=None):
    """Create all compounds with the rotational symmetry of a dodecahedron."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]),
                              angle=math.pi/9)
    polyh = S4A4.A5_E(base, 12, col_alt=3)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4A4.A5_C3(base, 5, col_alt=1)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/13)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.A5_C3(base, 10)
    polyh.rot_base(H_ACOS_1_3V5_8)
    save_off(polyh, '_mu3')
    polyh = S4A4.A5_C3(base, 5, col_alt=1)
    polyh.rot_base(ACOS_1_3V5_8)
    save_off(polyh, '_mu4')
    polyh = S4A4.A5_C3(
        base,
        20,
        cols=[
            S4A4.A4xI_C3.cols[1],
            S4A4.A4xI_C3.cols[2],
            S4A4.A4xI_C3.cols[2],
            S4A4.A4xI_C3.cols[10],
            S4A4.A4xI_C3.cols[4],
            S4A4.A4xI_C3.cols[5],
            S4A4.A4xI_C3.cols[8],
            S4A4.A4xI_C3.cols[3],
            S4A4.A4xI_C3.cols[7],
            S4A4.A4xI_C3.cols[5],
            S4A4.A4xI_C3.cols[8],
            S4A4.A4xI_C3.cols[1],
            S4A4.A4xI_C3.cols[4],
            S4A4.A4xI_C3.cols[0],
            S4A4.A4xI_C3.cols[6],
            S4A4.A4xI_C3.cols[6],
            S4A4.A4xI_C3.cols[3],
            S4A4.A4xI_C3.cols[7],
            S4A4.A4xI_C3.cols[0],
            S4A4.A4xI_C3.cols[10],
        ]
    )
    polyh.rot_base(ACOS_7_3V5_3_2_2V5_8)
    save_off(polyh, '_mu5')
    polyh = S4A4.A5_C3(
        base,
        20,
        cols=[
            S4A4.A4xI_C3.cols[0], #
            S4A4.A4xI_C3.cols[1], #
            S4A4.A4xI_C3.cols[6], #
            S4A4.A4xI_C3.cols[3], #
            S4A4.A4xI_C3.cols[10], #
            S4A4.A4xI_C3.cols[8], #
            S4A4.A4xI_C3.cols[7], #
            S4A4.A4xI_C3.cols[2], #
            S4A4.A4xI_C3.cols[1], #
            S4A4.A4xI_C3.cols[3], #
            S4A4.A4xI_C3.cols[8], #
            S4A4.A4xI_C3.cols[4], #
            S4A4.A4xI_C3.cols[9],
            S4A4.A4xI_C3.cols[2], #
            S4A4.A4xI_C3.cols[6], #
            S4A4.A4xI_C3.cols[4], #
            S4A4.A4xI_C3.cols[9],
            S4A4.A4xI_C3.cols[0], #
            S4A4.A4xI_C3.cols[7], #
            S4A4.A4xI_C3.cols[10],
        ]
    )
    polyh.rot_base(acos_7_3V5_16)
    save_off(polyh, '_mu6')

    polyh = S4A4.A5_C2(base, 5)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/11)  # example angle
    save_off(polyh)
    # special mu
    # There is a mu ~= 14.36 which looks like a 15 x D1C2 though not distinct ones. The reflection
    # --> could be related to angle math.acos(((V2+1)*V5 + V2-1)/6) of cube compounds (14.3592)
    # is part of a each pair in 10 x 3 | D3
    # There is a mu ~= 38.17 which looks like a 5 x D5C5, but there are no distinct 6 of these
    # Leave out for now
    # There is a mu ~= 22.47 what happens there?

    # TODO:
    # To find special angles: select one colour arrangement + variant and check whether the
    # sub-compound of one colour gets a higher symmetry
    # Include the multiplications

    # 6 x 5 | D10D5 / D2C2
    polyh = S4A4.A5_C2(base, 6, col_alt=1)
    polyh.rot_base(ATAN_V5_2)
    save_off(polyh, '_mu2')

    # 10 x 3 | D12D6 / D4D2
    polyh = S4A4.A5_C2(base, 10, col_alt=1)
    polyh.rot_base(ACOS_V5_1_2V3)
    save_off(polyh, '_mu3')

    # 10 x 3 | D6D3 / D2C2
    polyh = S4A4.A5_C2(base, 10)
    polyh.rot_base(ATAN_1_V5)
    save_off(polyh, '_mu4')

    # 6 x 5 | D20D10 / D4D2
    polyh = S4A4.A5_C2(base, 6)
    polyh.rot_base(ACOS_V_5_V5_V10)
    save_off(polyh, '_mu5')

    # Rigid compound
    polyh = S4A4.A5_A4(base, 5)
    save_off(polyh)


def create_a5xi(base, js_fd=None):
    """Create all compounds with the complete symmetry of a dodecahedron."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]),
                              angle=math.pi/9)
    polyh = S4A4.A5xI_E(base, 12, col_alt=3)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4A4.A5xI_C3(base, 5)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/13)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.A5xI_C3(base, 10, col_sym='D3xI')
    polyh.rot_base(H_ACOS_1_3V5_8)
    save_off(polyh, '_mu3')

    polyh = S4A4.A5xI_C2(base, 5)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/11)  # example angle
    save_off(polyh)

    polyh = S4A4.A5xI_C2C1(base, 6)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/9)  # example angle
    save_off(polyh)

    # Rigid compound
    polyh = S4A4.A5xI_A4(base, 5)
    save_off(polyh)

    polyh = S4A4.A5xI_D3C3('A', base, 5)
    save_off(polyh)

    polyh = S4A4.A5xI_D3C3('B', base, 5)
    save_off(polyh)

    polyh = S4A4.A5xI_D2C2(base, 5)
    save_off(polyh)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate off-files for compound polyhedra of polyhedra with tetrahedral "
        "symmetry"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="data/compounds/s4a4",
        help="Output directory to store off-models in. The whole path will be created if "
        "it doesn't exist."
    )
    args = parser.parse_args()

    # Create all models in one dir
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    os.chdir(args.output_dir)

    # TODO: from argument
    BASE = S4A4.tetrahedron

    # Create javascript file for models with rotational freedom
    with open("rotational_freedom.js", 'w') as FD:
        FD.write('// Compounds with rotational freedom\n')
        FD.write('// generated by Orbitit\n')

        create_a4(BASE, FD)
        create_a4xi(BASE, FD)
        create_s4a4(BASE, FD)
        create_s4(BASE, FD)
        create_s4xi(BASE, FD)
        create_a5(BASE, FD)
        create_a5xi(BASE, FD)
    print(f"Files saved in {args.output_dir}/")
