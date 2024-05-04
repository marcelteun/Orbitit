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


class CompoundS4xI():
    """Create set of files with compounds with a descriptive with S4xI symmetry."""

    final_sym = set({"A4xI", "S4xI", "A5xI"})

    def __init__(self, descr, output_dir, final_symmetry):
        self.descr = descr

        # Create all models in one dir
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        os.chdir(output_dir)

        # Create javascript file for models with rotational freedom
        with open("rotational_freedom.js", "w") as js_fd:
            js_fd.write("// Compounds with rotational freedom\n")
            js_fd.write("// generated by Orbitit\n")

            if not final_symmetry:
                self.create_a4xi(js_fd)
                self.create_s4xi(js_fd)
                self.create_a5xi(js_fd)
            else:
                {
                    "A4xI": self.create_a4xi,
                    "S4xI": self.create_s4xi,
                    "A5xI": self.create_a5xi,
                }[final_symmetry](js_fd)
        print(f"Files saved in {output_dir}/")

    def create_a4xi(self, js_fd=None):
        """Create all compounds with the symmetry of a tetrahedron and a cetral inversion."""
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 6)
        polyh = S4xI.A4xI_ExI(self.descr, 4, col_alt=2)
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        polyh = S4xI.A4xI_C2xI(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 6)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.A4xI_C2xI(self.descr, 3)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        polyh = S4xI.A4xI_C3xI(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(5 * math.pi / 18)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.A4xI_C3xI(self.descr, 4)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

    def create_s4xi(self, js_fd=None):
        """Create all compounds with the complete symmetry of a cube."""
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([2, 1, 0]), angle=math.pi / 2)
        polyh = S4xI.S4xI_ExI(self.descr, 4)
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        polyh = S4xI.S4xI_C2xI_A(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 3)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.S4xI_C2xI_A(self.descr, 4)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3.1")
        polyh = S4xI.S4xI_C2xI_A(self.descr, 6)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3.2")
        polyh = S4xI.S4xI_C2xI_A(self.descr, 3)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4.1")
        polyh = S4xI.S4xI_C2xI_A(self.descr, 4, col_alt=1)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4.2")
        polyh = S4xI.S4xI_C2xI_A(self.descr, 6)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        polyh = S4xI.S4xI_C2xI_B(self.descr, 6)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 3)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.S4xI_C2xI_B(self.descr, 4)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4xI.S4xI_C2xI_B(self.descr, 4, col_alt=1)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4xI.S4xI_C2xI_B(self.descr, 6)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4xI.S4xI_C2xI_B(self.descr, 4)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        polyh = S4xI.S4xI_D1xI(self.descr, 6)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 6)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.S4xI_D1xI(self.descr, 6, col_alt=1)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4xI.S4xI_D1xI(self.descr, 3, col_alt=1)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4xI.S4xI_D1xI(self.descr, 3, col_alt=2)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4xI.S4xI_D1xI(self.descr, 3, col_alt=1)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        polyh = S4xI.S4xI_C3xI(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(2 * math.pi / 9)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.S4xI_C3xI(self.descr, 4)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4xI.S4xI_C3xI(self.descr, 4)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")

        polyh = S4xI.S4xI_C4xI(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 12)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.S4xI_C4xI(self.descr, 3)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        # Rigid compounds
        polyh = S4xI.S4xI_S4xI(self.descr, 1)
        save_off(polyh)

        polyh = S4xI.S4xI_D4xI(self.descr, 3)
        save_off(polyh)

        polyh = S4xI.S4xI_D3xI(self.descr, 4)
        save_off(polyh)

        polyh = S4xI.S4xI_D2xI(self.descr, 3)
        save_off(polyh)

    def create_a5xi(self, js_fd=None):
        """Create all compounds with the complete symmetry of a dodecahedron."""
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 9)
        polyh = S4xI.A5xI_ExI(self.descr, 12, col_alt=3)
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        # 30A | A5 x I / C2 x I
        #######################################
        polyh = S4xI.A5xI_C2xI_A(self.descr, 6)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 7.3)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.A5xI_C2xI_A(self.descr, 15)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4xI.A5xI_C2xI_A(self.descr, 15)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")
        polyh = S4xI.A5xI_C2xI_A(self.descr, 10, col_alt=1)
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")
        polyh = S4xI.A5xI_C2xI_A(self.descr, 6)
        polyh.rot_base(polyh.mu[7])
        save_off(polyh, "_mu7")
        polyh = S4xI.A5xI_C2xI_A(self.descr, 6, col_alt=1)
        polyh.rot_base(polyh.mu[8])
        save_off(polyh, "_mu8")
        polyh = S4xI.A5xI_C2xI_A(self.descr, 10)
        polyh.rot_base(polyh.mu[9])
        save_off(polyh, "_mu9")
        polyh = S4xI.A5xI_C2xI_A(self.descr, 15)
        polyh.rot_base(polyh.mu[10])
        save_off(polyh, "_mu10")

        # 30B | A5 x I / C2 x I
        #######################################
        polyh = S4xI.A5xI_C2xI_B(self.descr, 6)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 7.3)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.A5xI_C2xI_B(self.descr, 6, col_alt=1)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4xI.A5xI_C2xI_B(self.descr, 10, col_alt=1)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4xI.A5xI_C2xI_B(self.descr, 10)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4xI.A5xI_C2xI_B(self.descr, 6)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")
        polyh = S4xI.A5xI_C2xI_B(self.descr, 15)
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")

        # 20 | A5 x I / C3 x I
        #######################################
        polyh = S4xI.A5xI_C3xI(self.descr, 5)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 7)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.A5xI_C3xI(self.descr, 5)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4xI.A5xI_C3xI(self.descr, 5)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4xI.A5xI_C3xI(self.descr, 5, col_alt=1)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5.1")
        polyh = S4xI.A5xI_C3xI(self.descr, 5)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5.2")
        polyh = S4xI.A5xI_C3xI(self.descr, 10)
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")

        # Rigid compound
        #######################################
        polyh = S4xI.A5xI_A4xI(self.descr, 5)
        save_off(polyh)

        polyh = S4xI.A5xI_D3xI("A", self.descr, 10)
        save_off(polyh)

        polyh = S4xI.A5xI_D3xI("B", self.descr, 10)
        save_off(polyh)

        polyh = S4xI.A5xI_D2xI(self.descr, 5)
        save_off(polyh)


if __name__ == "__main__":

    SYMMETRIES = CompoundS4xI.final_sym

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
        f"Must be one of {SYMMETRIES}.",
    )
    args = parser.parse_args()

    if not args.descriptive:
        DESCR = S4xI.cube
    else:
        with open(args.descriptive) as fd:
            shape = geom_3d.read_off_file(fd)
            DESCR = {
                "vs": shape.vs,
                "fs": shape.fs,
            }

    compounds = CompoundS4xI(DESCR, args.output_dir, args.final_symmetry)
