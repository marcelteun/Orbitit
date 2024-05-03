#!/usr/bin/env python
"""
Generate off-files for compound polyhedra of polyhedra with tetrahedral symmetra.
"""

# pylint: disable=too-many-statements

import argparse
import math
import os

from orbitit.compounds import S4xI
from orbitit import geomtypes, rgb


def save_off(comp, tail=""):
    """Save compound polyhedron in the OFF format.

    The filename will state the amount of elements and then use the compounds internal name.
    comp: the orbit.Shape object of the compound. From this the name and amount of constituents is
        used for the file name
    tail: this will be added to the end of the file name. Typically this is used to add the special
        angle in the case of a compound with rotational freedom.
    """
    # If this starts with a version then we need 2A_, 2B etc (not 2_A_)
    sep = "_" if comp.name[1] != "_" else ""
    with open(f"{comp.index}{sep}{comp.name}{tail}.off", "w") as fd:
        fd.write(comp.to_off())


def create_a4xi(base, js_fd=None):
    """Create all compounds with the symmetry of a tetrahedron and a cetral inversion."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 6)
    polyh = S4xI.A4xI_ExI(base, 4, col_alt=2)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4xI.A4xI_C2xI(base, 3)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi / 6)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.A4xI_C2xI(base, 3)
    polyh.rot_base(polyh.mu[2])
    save_off(polyh, "_mu2")

    polyh = S4xI.A4xI_C3xI(base, 4)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(5 * math.pi / 18)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.A4xI_C3xI(base, 4)
    polyh.rot_base(polyh.mu[2])
    save_off(polyh, "_mu2")


def create_s4xi(base, js_fd=None):
    """Create all compounds with the complete symmetry of a cube."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([2, 1, 0]), angle=math.pi / 2)
    polyh = S4xI.S4xI_ExI(base, 4)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    polyh = S4xI.S4xI_C2xI_A(base, 4)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi / 3)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.S4xI_C2xI_A(base, 4)
    polyh.rot_base(polyh.mu[3])
    save_off(polyh, "_mu3.1")
    polyh = S4xI.S4xI_C2xI_A(base, 6)
    polyh.rot_base(polyh.mu[3])
    save_off(polyh, "_mu3.2")
    polyh = S4xI.S4xI_C2xI_A(base, 3)
    polyh.rot_base(polyh.mu[4])
    save_off(polyh, "_mu4.1")
    polyh = S4xI.S4xI_C2xI_A(base, 4, col_alt=1)
    polyh.rot_base(polyh.mu[4])
    save_off(polyh, "_mu4.2")
    polyh = S4xI.S4xI_C2xI_A(base, 6)
    polyh.rot_base(polyh.mu[5])
    save_off(polyh, "_mu5")

    polyh = S4xI.S4xI_C2xI_B(base, 6)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi / 3)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.S4xI_C2xI_B(base, 4)
    polyh.rot_base(polyh.mu[2])
    save_off(polyh, "_mu2")
    polyh = S4xI.S4xI_C2xI_B(base, 4, col_alt=1)
    polyh.rot_base(polyh.mu[3])
    save_off(polyh, "_mu3")
    polyh = S4xI.S4xI_C2xI_B(base, 6)
    polyh.rot_base(polyh.mu[4])
    save_off(polyh, "_mu4")
    polyh = S4xI.S4xI_C2xI_B(base, 4)
    polyh.rot_base(polyh.mu[5])
    save_off(polyh, "_mu5")

    polyh = S4xI.S4xI_D1xI(base, 6)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi / 6)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.S4xI_D1xI(base, 6, col_alt=1)
    polyh.rot_base(polyh.mu[2])
    save_off(polyh, "_mu2")
    polyh = S4xI.S4xI_D1xI(base, 3, col_alt=1)
    polyh.rot_base(polyh.mu[3])
    save_off(polyh, "_mu3")
    polyh = S4xI.S4xI_D1xI(base, 3, col_alt=2)
    polyh.rot_base(polyh.mu[4])
    save_off(polyh, "_mu4")
    polyh = S4xI.S4xI_D1xI(base, 3, col_alt=1)
    polyh.rot_base(polyh.mu[5])
    save_off(polyh, "_mu5")

    polyh = S4xI.S4xI_C3xI(base, 4)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(2 * math.pi / 9)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.S4xI_C3xI(base, 4)
    polyh.rot_base(polyh.mu[2])
    save_off(polyh, "_mu2")
    polyh = S4xI.S4xI_C3xI(base, 4)
    polyh.rot_base(polyh.mu[3])
    save_off(polyh, "_mu3")

    polyh = S4xI.S4xI_C4xI(base, 3)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi / 12)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.S4xI_C4xI(base, 3)
    polyh.rot_base(polyh.mu[2])
    save_off(polyh, "_mu2")

    # Rigid compounds
    polyh = S4xI.S4xI_S4xI(base, 1)
    save_off(polyh)

    polyh = S4xI.S4xI_D4xI(base, 3)
    save_off(polyh)

    polyh = S4xI.S4xI_D3xI(base, 4)
    save_off(polyh)

    polyh = S4xI.S4xI_D2xI(base, 3)
    save_off(polyh)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate off-files for compound polyhedra of polyhedra with tetrahedral "
        "symmetry. Will also create a JS script file for the interactive models"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="data/compounds/s4xi",
        help="Output directory to store off-models in. The whole path will be created if "
        "it doesn't exist.",
    )
    args = parser.parse_args()

    # Create all models in one dir
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    os.chdir(args.output_dir)

    # TODO: from argument
    BASE = S4xI.cube

    # Create javascript file for models with rotational freedom
    with open("rotational_freedom.js", "w") as FD:
        FD.write("// Compounds with rotational freedom\n")
        FD.write("// generated by Orbitit\n")

        create_a4xi(BASE, FD)
        create_s4xi(BASE, FD)
    print(f"Files saved in {args.output_dir}/")
