#!/usr/bin/env python
"""Generate off-files for compound polyhedra"""
# pylint: disable=too-many-statements,too-many-lines

import math
import os

from orbitit.compounds import S4A4, S4xI
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
    # pylint: disable=redefined-outer-name
    with open(f"{comp.index}{sep}{comp.name}{tail}.off", "w") as fd:
        fd.write(comp.to_off())


class CompoundS4A4:
    """Create set of files with compounds with a descriptive with S4xI symmetry,

    E.g. a tetrahedron.
    """

    final_sym = set({"A4", "A4xI", "S4A4", "S4", "S4xI", "A5", "A5xI"})
    # Tetrahedron
    example_descriptive = {
        "vs": [
            geomtypes.Vec3([1, 1, 1]),
            geomtypes.Vec3([-1, -1, 1]),
            geomtypes.Vec3([1, -1, -1]),
            geomtypes.Vec3([-1, 1, -1]),
        ],
        "fs": [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]],
    }

    def __init__(self, descr, output_dir, final_symmetry, n=None):
        """
        n: a list with n-values to generate the cyclic and dihedral groups for.
        """
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
                self.create_a4(js_fd)
                self.create_a4xi(js_fd)
                self.create_s4a4(js_fd)
                self.create_s4(js_fd)
                self.create_s4xi(js_fd)
                self.create_a5(js_fd)
                self.create_a5xi(js_fd)
            else:
                {
                    "A4": self.create_a4,
                    "A4xI": self.create_a4xi,
                    "S4A4": self.create_s4a4,
                    "S4": self.create_s4,
                    "S4xI": self.create_s4xi,
                    "A5": self.create_a5,
                    "A5xI": self.create_a5xi,
                }[final_symmetry](js_fd)
        print(f"Files saved in {output_dir}/")

    def create_a4(self, js_fd=None):
        """Create all compounds with the A4 symmetry.

        A4 contains all rotational symmetries of a tetrahedron.
        """
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 4)
        polyh = S4A4.A4_E(self.descr, 4, col_alt=1)
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        polyh = S4A4.A4_C3(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        # example angle for which the compound is 5 | A5 / A4 with 1 removed
        polyh.rot_base(polyh.mu[2])
        save_off(polyh)

    def create_a4xi(self, js_fd=None):
        """Create all compounds with A4xI.

        A4xI contains the rotational symmetry of a tetrahedron and a cetral inversion.
        """
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 6)
        polyh = S4A4.A4xI_E(self.descr, 4, col_alt=2)
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        polyh = S4A4.A4xI_C3(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(5 * math.pi / 18)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.A4xI_C3(
            self.descr,
            4,
            cols=[
                S4A4.A4xI_C3.cols[0],
                S4A4.A4xI_C3.cols[1],
                S4A4.A4xI_C3.cols[1],
                S4A4.A4xI_C3.cols[0],
            ],
        )
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        polyh = S4A4.A4xI_C2C1(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 6)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.A4xI_C2C1(self.descr, 3)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

    def create_s4a4(self, js_fd=None):
        """Create all compounds with the complete symmetry of a tetrahedron."""
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 4)
        polyh = S4A4.S4A4_E(self.descr, 4, col_alt=0)
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        polyh = S4A4.S4A4_C4C2(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 6)  # example angle
        save_off(polyh)

        polyh = S4A4.S4A4_C3(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 5)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4A4_C3(self.descr, 4)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        polyh = S4A4.S4A4_C2C1(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 6)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4A4_C2C1(self.descr, 3)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")

        # Rigid compounds
        polyh = S4A4.S4A4_S4A4(self.descr, 1)
        save_off(polyh)

        polyh = S4A4.S4A4_D3C3(self.descr, 4)
        save_off(polyh)

    def create_s4(self, js_fd=None):
        """Create all compounds with the S4 symmetry: i.e. the rotational symmetry of a cube."""
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 1]), angle=2 * math.pi / 9)
        polyh = S4A4.S4_E(self.descr, 6, col_alt=2, col_sym="C4")
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        polyh = S4A4.S4_C3(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(polyh.mu[3])  # use special angle as example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4_C3(self.descr, 4)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4A4.S4_C3(self.descr, 4)
        polyh = S4A4.S4_C3(
            self.descr,
            8,
            cols=[
                S4A4.S4_C3.cols[0],
                S4A4.S4_C3.cols[0],
                S4A4.S4_C3.cols[1],
                S4A4.S4_C3.cols[1],
                S4A4.S4_C3.cols[2],
                S4A4.S4_C3.cols[2],
                S4A4.S4_C3.cols[3],
                S4A4.S4_C3.cols[3],
            ],
        )
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")

        polyh = S4A4.S4_C2(self.descr, 6)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(27.968 * math.pi / 180)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4_C2(self.descr, 4, col_alt=1)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4A4.S4_C2(self.descr, 4)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4A4.S4_C2(
            self.descr,
            12,
            cols=[
                S4A4.S4_C2.cols[0],
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
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4A4.S4_C2(
            self.descr,
            12,
            cols=[
                S4A4.S4_C2.cols[0],
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
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")
        polyh = S4A4.S4_C2(
            self.descr,
            12,
            cols=[
                rgb.gray,
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
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")

    def create_s4xi(self, js_fd=None):
        """Create all compounds with the S4xI symmetries, i.e. the complete symmetry of a cube."""
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([2, 1, 0]), angle=math.pi / 2)
        polyh = S4A4.S4xI_E(self.descr, 6, col_sym="C4xI")
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        polyh = S4A4.S4xI_C4C2(self.descr, 6, col_sym="C4xI")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 3)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4xI_C4C2(self.descr, 3)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        polyh = S4A4.S4xI_C3(self.descr, 4, col_sym="D3xI")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(2 * math.pi / 9)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4xI_C3(self.descr, 4, col_sym="D3xI")
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4A4.S4xI_C3(self.descr, 2, col_sym="S4")
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4A4.S4xI_C3(self.descr, 2, col_sym="A4xI")
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3_1")

        polyh = S4A4.S4xI_C2(self.descr, 6, col_sym="D2xI")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 9)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4xI_C2(self.descr, 4, col_alt=1)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4A4.S4xI_C2(self.descr, 4, col_alt=0)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4A4.S4xI_C2(self.descr, 6, col_sym="D2xI")
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4A4.S4xI_C2(
            self.descr,
            12,
            col_sym="C2xI",
            cols=[
                S4A4.A4xI_C3.cols[0],
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
            ],
        )
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")
        # FIXME: generated in a different order after upgrading Python
        polyh = S4A4.S4xI_C2(
            self.descr,
            24,
            col_sym="C2xI",
            cols=[
                S4A4.A4xI_C3.cols[0],
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
                S4A4.A4xI_C3.cols[3],
            ],
        )
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")
        # FIXME: generated in a different order after upgrading Python
        polyh = S4A4.S4xI_C2(
            self.descr,
            24,
            col_sym="C2xI",
            cols=[
                S4A4.A4xI_C3.cols[0],
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
                S4A4.A4xI_C3.cols[1],
            ],
        )
        polyh.rot_base(polyh.mu[7])
        save_off(polyh, "_mu7")

        polyh = S4A4.S4xI_C2C1(self.descr, 6, col_sym="D4C4")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(2 * math.pi / 9)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4xI_C2C1(self.descr, 6, col_sym="D2xI")
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4A4.S4xI_C2C1(self.descr, 3)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4A4.S4xI_C2C1(self.descr, 6, col_sym="D2xI")
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        polyh = S4A4.S4xI_D1C1(self.descr, 6, col_sym="D4C4")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(16 * math.pi / 180)  # example angle
        save_off(polyh)
        # special mu
        #            , , , math.pi/8, angle.ACOS_1_V3]
        polyh = S4A4.S4xI_D1C1(self.descr, 12, col_sym="D2C2", col_alt=2)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4A4.S4xI_D1C1(self.descr, 3, col_alt=1)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")
        polyh = S4A4.S4xI_D1C1(self.descr, 3)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")
        polyh = S4A4.S4xI_D1C1(self.descr, 3, col_alt=1)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        # Rigid compounds
        polyh = S4A4.S4xI_S4A4(self.descr, 2)
        save_off(polyh)

        polyh = S4A4.S4xI_D4D2(self.descr, 3)
        save_off(polyh)

        polyh = S4A4.S4xI_D3C3(self.descr, 4)
        save_off(polyh)

        polyh = S4A4.S4xI_D2C2(self.descr, 3)
        save_off(polyh)

    def create_a5(self, js_fd=None):
        """Create all compounds with the A5 symmetry, the rotational symmetry of a dodecahedron."""
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 9)
        polyh = S4A4.A5_E(self.descr, 12, col_alt=3)
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        # 40 | A5 / C3
        #######################################
        polyh = S4A4.A5_C3(self.descr, 5, col_alt=1)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 13)  # example angle
        save_off(polyh)
        # special mu
        # 10 x 2 | D6D3 / D3C3
        polyh = S4A4.A5_C3(self.descr, 10)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")

        # 5 x 4 | S4A4 / D3C3
        polyh = S4A4.A5_C3(self.descr, 5, col_alt=1)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")

        # 10 x 2 | D2C2 / C2C1
        polyh = S4A4.A5_C3(
            self.descr,
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
            ],
        )
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        # 10 x 2 | D3 / C3
        polyh = S4A4.A5_C3(
            self.descr,
            20,
            cols=[
                S4A4.A4xI_C3.cols[0],  #
                S4A4.A4xI_C3.cols[1],  #
                S4A4.A4xI_C3.cols[6],  #
                S4A4.A4xI_C3.cols[3],  #
                S4A4.A4xI_C3.cols[10],  #
                S4A4.A4xI_C3.cols[8],  #
                S4A4.A4xI_C3.cols[7],  #
                S4A4.A4xI_C3.cols[2],  #
                S4A4.A4xI_C3.cols[1],  #
                S4A4.A4xI_C3.cols[3],  #
                S4A4.A4xI_C3.cols[8],  #
                S4A4.A4xI_C3.cols[4],  #
                S4A4.A4xI_C3.cols[9],
                S4A4.A4xI_C3.cols[2],  #
                S4A4.A4xI_C3.cols[6],  #
                S4A4.A4xI_C3.cols[4],  #
                S4A4.A4xI_C3.cols[9],
                S4A4.A4xI_C3.cols[0],  #
                S4A4.A4xI_C3.cols[7],  #
                S4A4.A4xI_C3.cols[10],
            ],
        )
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")

        # 40 | A5 / C2
        #######################################
        polyh = S4A4.A5_C2(self.descr, 5)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 11)  # example angle
        save_off(polyh)
        # special mu
        # There is a mu ~= 14.36 which looks like a 15 x D1C2 though not distinct ones. The
        # reflection --> could be related to angle math.acos(((V2+1)*V5 + V2-1)/6) of cube compounds
        # (14.3592) is part of a each pair in 10 x 3 | D3
        # There is a mu ~= 38.17 which looks like a 5 x D5C5, but there are no distinct 6 of these
        # Leave out for now
        # There is a mu ~= 22.47 what happens there?

        # 6 x 5 | D10D5 / D2C2
        polyh = S4A4.A5_C2(self.descr, 6, col_alt=1)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        # 10 x 3 | D12D6 / D4D2
        polyh = S4A4.A5_C2(self.descr, 10, col_alt=1)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")

        # 10 x 3 | D6D3 / D2C2
        polyh = S4A4.A5_C2(self.descr, 10)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")

        # 6 x 5 | A5 / A4
        polyh = S4A4.A5_C2(self.descr, 6, col_alt=1)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        # 6 x 5 | D20D10 / D4D2
        polyh = S4A4.A5_C2(self.descr, 6)
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")

        # Rigid compound
        polyh = S4A4.A5_A4(self.descr, 5)
        save_off(polyh)

    def create_a5xi(self, js_fd=None):
        """Create all compounds with the A5xI: i.e. the complete symmetry of a dodecahedron."""
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 9)
        polyh = S4A4.A5xI_E(self.descr, 12, col_alt=3)
        polyh.transform_base(base_rot)
        save_off(polyh)
        if js_fd is not None:
            js_fd.write(polyh.to_js())

        # Rotation freedom (around 1 axis)
        # 40 | A5 x I / C3
        #######################################
        polyh = S4A4.A5xI_C3(self.descr, 5)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 13)  # example angle
        save_off(polyh)

        # special mu
        # 10 x 4 | D6 x I / D3C3
        polyh = S4A4.A5xI_C3(self.descr, 10, col_sym="D3xI")
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")

        # 5 x 8 | S4 x I / D3C3
        polyh = S4A4.A5xI_C3(self.descr, 5, col_sym="A4xI", col_alt=1)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")

        # 10 x 4 | C2 x I / E
        polyh = S4A4.A5xI_C3(
            self.descr,
            40,
            cols=[
                S4A4.A5xI_C3.cols[0],
                S4A4.A5xI_C3.cols[0],
                S4A4.A5xI_C3.cols[1],
                S4A4.A5xI_C3.cols[2],
                S4A4.A5xI_C3.cols[3],
                S4A4.A5xI_C3.cols[2],
                S4A4.A5xI_C3.cols[3],
                S4A4.A5xI_C3.cols[2],
                S4A4.A5xI_C3.cols[9],
                S4A4.A5xI_C3.cols[4],
                S4A4.A5xI_C3.cols[4],
                S4A4.A5xI_C3.cols[0],
                S4A4.A5xI_C3.cols[0],
                S4A4.A5xI_C3.cols[6],
                S4A4.A5xI_C3.cols[10],
                S4A4.A5xI_C3.cols[10],
                S4A4.A5xI_C3.cols[3],
                S4A4.A5xI_C3.cols[3],
                S4A4.A5xI_C3.cols[6],
                S4A4.A5xI_C3.cols[6],
                S4A4.A5xI_C3.cols[6],
                S4A4.A5xI_C3.cols[7],
                S4A4.A5xI_C3.cols[8],
                S4A4.A5xI_C3.cols[7],
                S4A4.A5xI_C3.cols[7],
                S4A4.A5xI_C3.cols[9],
                S4A4.A5xI_C3.cols[8],
                S4A4.A5xI_C3.cols[10],
                S4A4.A5xI_C3.cols[8],
                S4A4.A5xI_C3.cols[1],
                S4A4.A5xI_C3.cols[9],
                S4A4.A5xI_C3.cols[7],
                S4A4.A5xI_C3.cols[1],
                S4A4.A5xI_C3.cols[1],
                S4A4.A5xI_C3.cols[9],
                S4A4.A5xI_C3.cols[10],
                S4A4.A5xI_C3.cols[2],
                S4A4.A5xI_C3.cols[4],
                S4A4.A5xI_C3.cols[4],
                S4A4.A5xI_C3.cols[8],
            ],
        )
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        # 5 x 8 | A4 x I / C3 | mu2
        polyh = S4A4.A5xI_C3(self.descr, 5, col_sym="A4xI", col_alt=1)
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")

        # 60 | A5 x I / C2
        #######################################
        polyh = S4A4.A5xI_C2(self.descr, 5)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 11)  # example angle
        save_off(polyh)

        # special mu
        # 6 x 10 | D10xI / D2C2
        polyh = S4A4.A5xI_C2(self.descr, 6, col_alt=1)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        # 10 x 6 | D12xI / D4D2
        polyh = S4A4.A5xI_C2(self.descr, 10, col_sym="D3xI", col_alt=1)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")

        # 10 x 6 | D6xI / D2C2
        polyh = S4A4.A5xI_C2(self.descr, 10, col_sym="D3xI")
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4")

        # 6 x 10 | A5xI / A4
        polyh = S4A4.A5xI_C2(self.descr, 6, col_alt=1)
        polyh.rot_base(polyh.mu[5])
        save_off(polyh, "_mu5")

        # 6 x 10 | D20xI / D4D2
        polyh = S4A4.A5xI_C2(self.descr, 6)
        polyh.rot_base(polyh.mu[6])
        save_off(polyh, "_mu6")

        # 10 x 6 | S4xI / D4D2
        polyh = S4A4.A5xI_C2(self.descr, 10, col_sym="D3xI")
        polyh.rot_base(polyh.mu[7])
        save_off(polyh, "_mu7")

        # 30 x 2 | D3C3 / C3
        polyh = S4A4.A5xI_C2(self.descr, 10, col_sym="D3xI", col_alt=1)
        polyh.rot_base(polyh.mu[8])
        save_off(polyh, "_mu8")

        # 60 | A5 x I / C2C1
        #######################################
        polyh = S4A4.A5xI_C2C1(self.descr, 6)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.rot_base(math.pi / 9)  # example angle
        save_off(polyh)

        # Rigid compound
        #######################################
        polyh = S4A4.A5xI_A4(self.descr, 5)
        save_off(polyh)

        polyh = S4A4.A5xI_D3C3("A", self.descr, 5)
        save_off(polyh)

        polyh = S4A4.A5xI_D3C3("B", self.descr, 5)
        save_off(polyh)

        polyh = S4A4.A5xI_D2C2(self.descr, 5)
        save_off(polyh)


class CompoundS4xI:
    """Create set of files with compounds with a descriptive with S4xI symmetry."""

    final_sym = set({"CnxI", "A4xI", "S4xI", "A5xI"})
    # Cube
    example_descriptive = {
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

    def __init__(self, descr, output_dir, final_symmetry, n=None):
        """
        n: a list with n-values to generate the cyclic and dihedral groups for.
        """
        self.descr = descr

        if n:
            self.n = n
        else:
            self.n = []
        # Create all models in one dir
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        os.chdir(output_dir)

        # Create javascript file for models with rotational freedom
        with open("rotational_freedom.js", "w") as js_fd:
            js_fd.write("// Compounds with rotational freedom\n")
            js_fd.write("// generated by Orbitit\n")

            if not final_symmetry:
                self.create_cnxi(js_fd)
                self.create_a4xi(js_fd)
                self.create_s4xi(js_fd)
                self.create_a5xi(js_fd)
            else:
                {
                    "CnxI": self.create_cnxi,
                    "A4xI": self.create_a4xi,
                    "S4xI": self.create_s4xi,
                    "A5xI": self.create_a5xi,
                }[final_symmetry](js_fd)
        print(f"Files saved in {output_dir}/")

    def create_cnxi(self, js_fd=None):
        # example rotation
        for n in self.n:
            base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 6)
            polyh = S4xI.CnxI_ExI(self.descr, n, n)
            polyh.transform_base(base_rot)
            save_off(polyh)
            if js_fd is not None:
                js_fd.write(polyh.to_js())

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