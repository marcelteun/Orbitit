#!env python
from __future__ import print_function

import math
import os

from compounds import S4A4
import geomtypes


def save_off(comp):
    with open('{}_{}.off'.format(comp.index, comp.name), 'w') as fd:
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
    a4_c3 = S4A4.A4_C3(base, 4)
    # example angle for which the compound is 5 | A5 / A4 with 1 removed
    a4_c3.rot_base(math.acos((-1 + 3 * math.sqrt(5))/8))
    save_off(a4_c3)
    if js_fd is not None:
        js_fd.write(polyh.to_js())


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
