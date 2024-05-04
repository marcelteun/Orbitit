#!/usr/bin/env python
"""
Generate off-files for compound polyhedra of polyhedra with tetrahedral symmetra.
"""

# pylint: disable=too-many-statements

import argparse
import math
import os

from orbitit.compounds import S4xI
from orbitit import geom_3d, geomtypes


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
    # pylint: disable=redefined-outer-name
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


def create_a5xi(base, js_fd=None):
    """Create all compounds with the complete symmetry of a dodecahedron."""
    # example rotation
    base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 9)
    polyh = S4xI.A5xI_ExI(base, 12, col_alt=3)
    polyh.transform_base(base_rot)
    save_off(polyh)
    if js_fd is not None:
        js_fd.write(polyh.to_js())

    # Rotation freedom (around 1 axis)
    # 30A | A5 x I / C2 x I
    #######################################
    polyh = S4xI.A5xI_C2xI_A(base, 6)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi / 7.3)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.A5xI_C2xI_A(base, 15)
    polyh.rot_base(polyh.mu[4])
    save_off(polyh, "_mu4")
    polyh = S4xI.A5xI_C2xI_A(base, 15)
    polyh.rot_base(polyh.mu[5])
    save_off(polyh, "_mu5")
    polyh = S4xI.A5xI_C2xI_A(base, 10, col_alt=1)
    polyh.rot_base(polyh.mu[6])
    save_off(polyh, "_mu6")
    polyh = S4xI.A5xI_C2xI_A(base, 6)
    polyh.rot_base(polyh.mu[7])
    save_off(polyh, "_mu7")
    polyh = S4xI.A5xI_C2xI_A(base, 6, col_alt=1)
    polyh.rot_base(polyh.mu[8])
    save_off(polyh, "_mu8")
    polyh = S4xI.A5xI_C2xI_A(base, 10)
    polyh.rot_base(polyh.mu[9])
    save_off(polyh, "_mu9")
    polyh = S4xI.A5xI_C2xI_A(base, 15)
    polyh.rot_base(polyh.mu[10])
    save_off(polyh, "_mu10")

    # 30B | A5 x I / C2 x I
    #######################################
    polyh = S4xI.A5xI_C2xI_B(base, 6)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi / 7.3)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.A5xI_C2xI_B(base, 6, col_alt=1)
    polyh.rot_base(polyh.mu[2])
    save_off(polyh, "_mu2")
    polyh = S4xI.A5xI_C2xI_B(base, 10, col_alt=1)
    polyh.rot_base(polyh.mu[3])
    save_off(polyh, "_mu3")
    polyh = S4xI.A5xI_C2xI_B(base, 10)
    polyh.rot_base(polyh.mu[4])
    save_off(polyh, "_mu4")
    polyh = S4xI.A5xI_C2xI_B(base, 6)
    polyh.rot_base(polyh.mu[5])
    save_off(polyh, "_mu5")
    polyh = S4xI.A5xI_C2xI_B(base, 15)
    polyh.rot_base(polyh.mu[6])
    save_off(polyh, "_mu6")

    # 20 | A5 x I / C3 x I
    #######################################
    polyh = S4xI.A5xI_C3xI(base, 5)
    if js_fd is not None:
        js_fd.write(polyh.to_js())
    polyh.rot_base(math.pi / 7)  # example angle
    save_off(polyh)
    # special mu
    polyh = S4xI.A5xI_C3xI(base, 5)
    polyh.rot_base(polyh.mu[3])
    save_off(polyh, "_mu3")
    polyh = S4xI.A5xI_C3xI(base, 5)
    polyh.rot_base(polyh.mu[4])
    save_off(polyh, "_mu4")
    polyh = S4xI.A5xI_C3xI(base, 5, col_alt=1)
    polyh.rot_base(polyh.mu[5])
    save_off(polyh, "_mu5.1")
    polyh = S4xI.A5xI_C3xI(base, 5)
    polyh.rot_base(polyh.mu[5])
    save_off(polyh, "_mu5.2")
    polyh = S4xI.A5xI_C3xI(base, 10)
    polyh.rot_base(polyh.mu[6])
    save_off(polyh, "_mu6")

    # Rigid compound
    #######################################
    polyh = S4xI.A5xI_A4xI(base, 5)
    save_off(polyh)

    polyh = S4xI.A5xI_D3xI("A", base, 10)
    save_off(polyh)

    polyh = S4xI.A5xI_D3xI("B", base, 10)
    save_off(polyh)

    polyh = S4xI.A5xI_D2xI(base, 5)
    save_off(polyh)


if __name__ == "__main__":

    SYMMETRY = {
        "A4xI": create_a4xi,
        "S4xI": create_s4xi,
        "A5xI": create_a5xi,
    }
    parser = argparse.ArgumentParser(
        description="Generate off-files for compound polyhedra of polyhedra with tetrahedral "
        "symmetry. Will also create a JS script file for the interactive models"
    )
    parser.add_argument(
        "-d",
        "--descriptive",
        help="The .off file for the descriptive, i.e. what you want to make a compound of. "
        "It should have the correct symmetry and it should be positioned in the standard way, "
        "I.e. for cube symmetry the 4-fold axes should be along the coordinate axes, "
        "and for tetrahedron and icosahedron symmetry the 2-fold axis should be along the "
        "z-axis. "
        "For all those symmetries, the 3-fold axis is along [1, 1, 1]. "
        "For the cyclic and the dihedral symmetries the n-fold axis is along the z-axis. "
        "Note that the script will not verify that this is the case. "
        "If not specified, then the cube is used. ",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="data/compounds/s4xi",
        help="Output directory to store off-models in. The whole path will be created if "
        "it doesn't exist.",
    )
    parser.add_argument(
        "-f",
        "--final-symmetry",
        help="Specify this to only generate compounds having one symmetry group. "
        f"Must be one of {list(SYMMETRY.keys())}.",
    )
    args = parser.parse_args()

    # Create all models in one dir
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    os.chdir(args.output_dir)

    if not args.descriptive:
        descr = S4xI.cube
    else:
        with open(args.descriptive) as fd:
            shape = geom_3d.read_off_file(fd)
            descr = {
                "vs": shape.vs,
                "fs": shape.fs,
            }

    # Create javascript file for models with rotational freedom
    with open("rotational_freedom.js", "w") as fd:
        fd.write("// Compounds with rotational freedom\n")
        fd.write("// generated by Orbitit\n")

        if not args.final_symmetry:
            create_a4xi(descr, fd)
            create_s4xi(descr, fd)
            create_a5xi(descr, fd)
        else:
            SYMMETRY[args.final_symmetry](descr, fd)
    print(f"Files saved in {args.output_dir}/")
