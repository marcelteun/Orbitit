#!/usr/bin/env python
from __future__ import print_function

import math
import os

from compounds import S4A4
import geomtypes

V2 = math.sqrt(2)
V3 = math.sqrt(3)
V5 = math.sqrt(5)
ACOS__1_3V5_8 = math.acos((-1 + 3 * V5) / 8)
ASIN_1_V3 = math.asin(1 / V3)
ACOS_1_V3 = math.acos(1 / V3)
ATAN_4V2_7 = math.atan(4 * V2 / 7)


def save_off(comp, tail=''):
    # If this starts with a version then we need 2A_, 2B etc (not 2_A_)
    sep = '_' if comp.name[1] != '_' else ''
    with open('{}{}{}{}.off'.format(comp.index,
                                    sep, comp.name, tail), 'w') as fd:
        fd.write(comp.to_off())


def create_a4(base, js_fd=None):
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
    polyh.rot_base(math.acos((-1 + 3 * math.sqrt(5))/8))
    save_off(polyh)


def create_a4xi(base, js_fd=None):
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
    polyh.rot_base(ACOS__1_3V5_8)
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
    polyh.rot_base(44.48 * math.pi / 180)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4_C3(base, 4)
    polyh.rot_base(math.pi/6)
    save_off(polyh, '_mu2')

    polyh = S4A4.S4_C2(base, 6)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(22.7 * math.pi / 180)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4A4.S4_C2(base, 4, col_alt=1)
    polyh.rot_base(9.74 * math.pi / 180)  # TODO calculate algebraicly
    save_off(polyh, '_mu2')


def create_s4xi(base, js_fd=None):
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
                         cols=[S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[0],
                               S4A4.A4xI_C3.cols[2],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[1],
                               S4A4.A4xI_C3.cols[3],
                               S4A4.A4xI_C3.cols[0],
                               ])
    polyh.rot_base(ATAN_4V2_7 / 2)
    save_off(polyh, '_mu5')

    polyh = S4A4.S4xI_C2C1(base, 6, col_sym='D4C4')
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(2*math.pi/9)  # example angle
    save_off(polyh)

    polyh = S4A4.S4xI_D1C1(base, 6, col_sym='D4C4')
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(16 * math.pi / 180)  # example angle
    save_off(polyh)

    # Rigid compounds
    polyh = S4A4.S4xI_S4A4(base, 2)
    save_off(polyh)

    polyh = S4A4.S4xI_D4D2(base, 3)
    save_off(polyh)

    polyh = S4A4.S4xI_D3C3(base, 2)
    save_off(polyh)

    polyh = S4A4.S4xI_D2C2(base, 3)
    save_off(polyh)


def create_a5(base, js_fd=None):
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]),
                              angle=math.pi/9)
    polyh = S4A4.A5_E(base, 12, col_alt=3)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4A4.A5_C3(base, 5)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/13)  # example angle
    save_off(polyh)

    polyh = S4A4.A5_C2(base, 5)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi/11)  # example angle
    save_off(polyh)

    # Rigid compound
    polyh = S4A4.A5_A4(base, 5)
    save_off(polyh)


def create_a5xi(base, js_fd=None):
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

    # TODO: from argument
    out_dir = 'data/compounds/s4a4'
    js_file = 'rotational_freedom.js'

    # Create all models in one dir
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    os.chdir(out_dir)

    # TODO: from argument
    base = S4A4.tetrahedron

    # Create javascript file for models with rotational freedom
    with open(js_file, 'w') as fd:
        fd.write('// Compounds with rotational freedom\n')
        fd.write('// generated by Orbitit\n')

        create_a4(base, fd)
        create_a4xi(base, fd)
        create_s4a4(base, fd)
        create_s4(base, fd)
        create_s4xi(base, fd)
        create_a5(base, fd)
        create_a5xi(base, fd)
