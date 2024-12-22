#!/usr/bin/env python
"""Generate off-files for compound polyhedra"""
# pylint: disable=too-many-statements,too-many-lines

import math
import os

from orbitit.compounds import S4A4, S4xI
from orbitit import geomtypes, rgb


def get_stem(comp, tail=""):
    """Construct a stem to be used for a filename and return it.

    The filename will state the amount of elements and then use the compounds internal name.
    comp: the orbit.Shape object of the compound. From this the name and amount of constituents is
        used for the file name
    tail: this will be added to the end of the file name. Typically this is used to add the special
        angle in the case of a compound with rotational freedom.

    Return: the stem, i.e. filename without extension.
    """
    # If this starts with a version then we need 2A_, 2B etc (not 2_A_)
    sep = "_" if comp.name[1] != "_" else ""
    # pylint: disable=redefined-outer-name
    return f"{comp.index}{sep}{comp.name}{tail}"


def save_off(comp, tail=""):
    """Save compound polyhedron in the OFF format.

    comp: the orbit.Shape object of the compound. From this the name and amount of constituents is
        used for the file name
    tail: this will be added to the end of the file name. Typically this is used to add the special
        angle in the case of a compound with rotational freedom.
    """
    with open(get_stem(comp, tail) + ".off", "w") as fd:
        fd.write(comp.to_off())


class CompoundS4A4:
    """Create set of files with compounds with a descriptive with S4xI symmetry,

    E.g. a tetrahedron.
    """

    final_sym = set(
        {
            "A4", "A4xI", "S4A4", "S4", "S4xI", "A5", "A5xI", "Cn", "C2nCn", "CnxI", "DnCn", "Dn",
            "D2nDn", "DnxI",
        }
    )
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

    # default orientation of the descriptive for general cyclic and dihedral symmetries.
    _eg_rotate = geomtypes.Rot3(axis=geomtypes.Vec3([-1, 2, -5]), angle=math.pi / 3)
    _eg_descr = None
    # by default create dihedral and cyclic compounds for the specified n-fold axis:
    _no_of = [1, 2, 3, 4, 5]

    def __init__(self, descr, output_dir, final_symmetry=None, no_of=None, rot=None):
        """
        Initialize compounds of polyhedra with tetrahedron symmetry.

        descr: specify the descriptive here. It is a dictionary with the following fields:
               - "vs": which is a list of geomtypes.Vec3 values specifing the vertices.
               - "fs": which is a list of faces where each face is a list of vertex indices from
                       "vs".
            The descriptive is supposed to have tetrahedron symmetry (S4A4) in its standard
            orientation, where X-, Y-, and Z-axis are the 2-fold symmetry axes.
        output_dir: specify where to save all the files. If this directory doesn't exist it is
            created.
        final_symmetry: a string specifying which final symmetry should be generated immediately. If
            nothing is specified then nothing is generated. Call generate_compounds separately to
            generate the compounds.
        no_of: starting from 1 specify for which number in the list of valid n-fold symmetry axes to
            generated models for the cyclic and dihedral symmetry groups.
        rot: the descriptive will be rotated as according to the specified geomtypes.Rot3 for the
            generated models where the descriptive doesn't share any symmetries witrh the final
            symmetry (for any of them).
        """
        self.descr = descr
        self.output_dir = output_dir

        # Create all models in one dir
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        os.chdir(output_dir)

        if rot is None:
            self.transform_descr(self._eg_rotate)
        else:
            self.transform_descr(rot)

        if no_of:
            self.no_of = no_of
        else:
            self.no_of = self._no_of

        self.create = {
            "A4": self.create_a4,
            "A4xI": self.create_a4xi,
            "S4A4": self.create_s4a4,
            "S4": self.create_s4,
            "S4xI": self.create_s4xi,
            "A5": self.create_a5,
            "A5xI": self.create_a5xi,
            "Cn": self.create_cn,
            "C2nCn": self.create_c2ncn,
            "CnxI": self.create_cnxi,
            "DnCn": self.create_dncn,
            "Dn": self.create_dn,
            "D2nDn": self.create_d2ndn,
            "DnxI": self.create_dnxi,
        }
        # TODO: call this actively (always for all generators)
        #if final_symmetry is not None:
        self.generate_compounds(final_symmetry)

    def transform_descr(self, rot):
        """Create a rotated descriptive for the cyclic and dihedral symmetries.

        rot: a geomtypes.Rot3 specifying a 3D rotation.
        """

        self._eg_descr = {
            "vs": [rot * v for v in self.descr["vs"]],
            "fs": self.descr["fs"],
        }

    def generate_compounds(self, final_symmetry=None):
        """
        Generate the compounds polyhedra for the specified symmetry

        final_symmetry: the final symmetry of the generated compounds. If nothing specified, then
            all symmetries will be generated. This might take some time.
        """
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
                self.create_cn(js_fd)
                self.create_c2ncn(js_fd)
                self.create_cnxi(js_fd)
                self.create_dncn(js_fd)
                self.create_dn(js_fd)
                self.create_d2ndn(js_fd)
                self.create_dnxi(js_fd)
            else:
                self.create[final_symmetry](js_fd)

        print(f"Files saved in {self.output_dir}/")

    def create_a4(self, js_fd=None):
        """Create all compounds with the A4 symmetry.

        A4 contains all rotational symmetries of a tetrahedron.
        """
        polyh = S4A4.A4_E(self.descr, 4, col_alt=1)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 4)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        polyh = S4A4.A4_C3(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example angle for which the compound is 5 | A5 / A4 with 1 removed
        polyh.rot_base(polyh.mu[2])
        save_off(polyh)
        # also save as special angle
        save_off(polyh, "_mu2")

    def create_a4xi(self, js_fd=None):
        """Create all compounds with A4xI.

        A4xI contains the rotational symmetry of a tetrahedron and a cetral inversion.
        """
        polyh = S4A4.A4xI_E(self.descr, 4, col_alt=2)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 6)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        polyh = S4A4.A4xI_C3(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
        polyh.rot_base(math.pi / 6)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.A4xI_C2C1(self.descr, 3)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

    def create_s4a4(self, js_fd=None):
        """Create all compounds with the complete symmetry of a tetrahedron."""
        polyh = S4A4.S4A4_E(self.descr, 4, col_alt=0)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 4)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        polyh = S4A4.S4A4_C4C2(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        polyh.rot_base(math.pi / 6)  # example angle
        save_off(polyh)

        polyh = S4A4.S4A4_C3(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        polyh.rot_base(math.pi / 5)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4A4_C3(self.descr, 4)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        polyh = S4A4.S4A4_C2C1(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh = S4A4.S4_E(self.descr, 6, col_alt=2, col_sym="C4")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 1]), angle=2 * math.pi / 9)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        polyh = S4A4.S4_C3(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh = S4A4.S4xI_E(self.descr, 6, col_sym="C4xI")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([2, 1, 0]), angle=math.pi / 2)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        polyh = S4A4.S4xI_C4C2(self.descr, 6, col_sym="C4xI")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        polyh.rot_base(math.pi / 3)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4A4.S4xI_C4C2(self.descr, 3)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        polyh = S4A4.S4xI_C3(self.descr, 4, col_sym="D3xI")
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh = S4A4.A5_E(self.descr, 12, col_alt=3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 9)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        # 40 | A5 / C3
        #######################################
        polyh = S4A4.A5_C3(self.descr, 5, col_alt=1)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh = S4A4.A5xI_E(self.descr, 12, col_alt=3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 9)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        # 40 | A5 x I / C3
        #######################################
        polyh = S4A4.A5xI_C3(self.descr, 5)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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

    def create_cn(self, js_fd=None, no_of=None):
        """Create all compounds with the Cn symmetry.

        The Cn symmetry consists of pure cyclic symmetries where the n-fold symmetry axis is the
        Z-axis.

        js_fd: file descriptor to the JavaScript file for the models using a slide-bar.
        no_of: starting from 1 specify for which number in the list of valid n-fold symmetry axes to
            generated models for the cyclic and dihedral symmetry groups. This will overwrite the
            value specified during initialisation.
        """
        if no_of is None:
            no_of = self.no_of
        for i in no_of:
            n = i + 1
            polyh = S4A4.Cn_E(n, self._eg_descr, n)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            # example rotation
            base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 3)
            polyh.transform_base(base_rot)
            save_off(polyh)

    def create_c2ncn(self, js_fd=None, no_of=None):
        """Create all compounds with the CnxI symmetry.

        The C2nCn symmetry consists of pure cyclic symmetries where the n-fold symmetry axis is the
        Z-axis.

        Note for n = 1 CnxI consists of {E, S}

        js_fd: file descriptor to the JavaScript file for the models using a slide-bar.
        no_of: starting from 1 specify for which number in the list of valid n-fold symmetry axes to
            generated models for the cyclic and dihedral symmetry groups. This will overwrite the
            value specified during initialisation.
        """
        if no_of is None:
            no_of = self.no_of
        for n in no_of:
            no_of_cols = 2 if n == 1 else n
            polyh = S4A4.C2nCn_E(n, self._eg_descr, no_of_cols)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            # example rotation
            base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 3)
            polyh.transform_base(base_rot)
            save_off(polyh)

    def create_cnxi(self, js_fd=None, no_of=None):
        """Create all compounds with the CnxI symmetry.

        The CnxI symmetry consists of pure cyclic symmetries where the n-fold symmetry axis is the
        Z-axis and all those multiplied with the central inversion.

        Note for n = 1 CnxI consists of {E, I}. When using the a descriptive with S4A4 symmetry,
        e.g. a tetrahedron, then a higher symmetry is obtained. In the case of a tetrahedron it is
        the Stella Octangula, which is a rigid compound. For this reason if no_of equals to 1, then
        n=2 is used.

        js_fd: file descriptor to the JavaScript file for the models using a slide-bar.
        no_of: starting from 1 specify for which number in the list of valid n-fold symmetry axes to
            generated models for the cyclic and dihedral symmetry groups. This will overwrite the
            value specified during initialisation.
        """
        if no_of is None:
            no_of = self.no_of
        for i in no_of:
            n = i + 1
            polyh = S4A4.CnxI_E(n, self._eg_descr, n)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            # example rotation
            base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 3)
            polyh.transform_base(base_rot)
            save_off(polyh)

    def create_dncn(self, js_fd=None, no_of=None):
        """Create all compounds with the DnCn symmetry.

        The DnCn symmetry has an n-fold rotation axis and n reflection planes that share the n-fold
        axis.

        Note for n = 1 D1C1 is obtained which is isomorph to C2C1, i.e. it consists of {E, S}. Use
        that symmetry instead.

        js_fd: file descriptor to the JavaScript file for the models using a slide-bar.
        no_of: starting from 1 specify for which number in the list of valid n-fold symmetry axes to
            generated models for the cyclic and dihedral symmetry groups. This will overwrite the
            value specified during initialisation.
        """
        if no_of is None:
            no_of = self.no_of
        for i in no_of:
            n = i + 1
            polyh = S4A4.DnCn_E(n, self._eg_descr, n)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            # example rotation
            base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 3)
            polyh.transform_base(base_rot)
            save_off(polyh)

            # Rigid compound
            #######################################
            polyh = S4A4.D3nC3n_D3C3(n, self.descr, n)
            save_off(polyh)

    def create_dn(self, js_fd=None, no_of=None):
        """Create all compounds with the Dn symmetry.

        The Dn symmetry has an n-fold rotation axis and n 2-fold axes meeting the n-fold axis
        orthogonally in one point.

        Note for n = 1 D1 is obtained which is isomorph to C2. Use that symmetry instead.

        js_fd: file descriptor to the JavaScript file for the models using a slide-bar.
        no_of: starting from 1 specify for which number in the list of valid n-fold symmetry axes to
            generated models for the cyclic and dihedral symmetry groups. This will overwrite the
            value specified during initialisation.
        """
        if no_of is None:
            no_of = self.no_of
        for i in no_of:
            n = i + 1
            polyh = S4A4.Dn_E(n, self._eg_descr, n)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            # example rotation
            base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 3)
            polyh.transform_base(base_rot)
            save_off(polyh)

    def create_d2ndn(self, js_fd=None, no_of=None):
        """Create all compounds with the D2nDn symmetry.

        The D2nDn symmetry has an n-fold rotation axis and n 2-fold axes meeting the n-fold axis
        orthogonally in one point and n reflecion planes sharing the n-fold axis.
        For even n the 2-fold axes are between the reflection planes for odd n the 2-fold axes ly in
        the reflection planes and there is one extra reflection plane orthogonal to the n-fold axis.

        Note for n = 1 D2D1 is obtained which is isomorph to D2C2. Use that symmetry instead.

        js_fd: file descriptor to the JavaScript file for the models using a slide-bar.
        no_of: starting from 1 specify for which number in the list of valid n-fold symmetry axes to
            generated models for the cyclic and dihedral symmetry groups. This will overwrite the
            value specified during initialisation.
        """
        if no_of is None:
            no_of = self.no_of
        for i in no_of:
            n = i + 1
            polyh = S4A4.D2nDn_E(n, self._eg_descr, n)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            # example rotation
            base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 3)
            polyh.transform_base(base_rot)
            save_off(polyh)

            # Rigid compound
            #######################################
            m = 2 * i + 1
            polyh = S4A4.D2nDn_D2C2(m, self.descr, m)
            save_off(polyh)

            polyh = S4A4.D4nD2n_D4D2(m, self.descr, m)
            save_off(polyh)

            polyh = S4A4.D6nD3n_D3C3(n, self.descr, 2)
            save_off(polyh)

    def create_dnxi(self, js_fd=None, no_of=None):
        """Create all compounds with the DnxI symmetry.

        The DnxI symmetry has an n-fold rotation axis and n 2-fold axes meeting the n-fold axis
        orthogonally in one point and n reflecion planes sharing the n-fold axis. Obviously they all
        include the central inversion I. For odd n the 2-fold axes are between the reflection planes
        for even n the 2-fold axes ly in the reflection planes and there is one extra reflection
        plane orthogonal to the n-fold axis.

        Note for n = 1 D1xI is obtained which is isomorph to C2xI. Use that symmetry instead.

        js_fd: file descriptor to the JavaScript file for the models using a slide-bar.
        no_of: starting from 1 specify for which number in the list of valid n-fold symmetry axes to
            generated models for the cyclic and dihedral symmetry groups. This will overwrite the
            value specified during initialisation.
        """
        if no_of is None:
            no_of = self.no_of
        for i in no_of:
            n = i + 1
            polyh = S4A4.DnxI_E(n, self._eg_descr, n)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            # example rotation
            base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 3)
            polyh.transform_base(base_rot)
            save_off(polyh)

            # Rigid compound
            #######################################
            polyh = S4A4.D2nxI_D2C2(n, self.descr, n)
            save_off(polyh)

            polyh = S4A4.D3nxI_D3C3(n, self.descr, n)
            save_off(polyh)

            polyh = S4A4.D4nxI_D4D2(n, self.descr, n)
            save_off(polyh)


class CompoundS4xI:
    """Create set of files with compounds with a descriptive with S4xI symmetry."""

    final_sym = set({"CnxI", "DnxI", "A4xI", "S4xI", "A5xI"})
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

    def __init__(self, descr, output_dir, final_symmetry=None, no_of=None):
        """
        Initialize compounds of polyhedra with cube symmetry.

        descr: specify the descriptive here. It is a dictionary with the following fields:
               - "vs": which is a list of geomtypes.Vec3 values specifing the vertices.
               - "fs": which is a list of faces where each face is a list of vertex indices from
                       "vs".
            The descriptive is supposed to have cube symmetry (S4xI) in its standard orientation,
            where X-, Y-, and Z-axis are the 4-fold symmetry axes.
        output_dir: specify where to save all the files. If this directory doesn't exist it is
            created.
        final_symmetry: a string specifying which final symmetry should be generated immediately. If
            nothing is specified then nothing is generated. Call generate_compounds separately to
            generate the compounds.
        no_of: specify for which n in n-fold symmetry axis to generated models for the cyclic and
            dihedral symmetry groups.
        """
        self.descr = descr

        if no_of:
            self.no_of = no_of
        else:
            self.no_of = []
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
                self.create_dnxi(js_fd)
                self.create_a4xi(js_fd)
                self.create_s4xi(js_fd)
                self.create_a5xi(js_fd)
            else:
                {
                    "CnxI": self.create_cnxi,
                    "DnxI": self.create_dnxi,
                    "A4xI": self.create_a4xi,
                    "S4xI": self.create_s4xi,
                    "A5xI": self.create_a5xi,
                }[final_symmetry](js_fd)
        print(f"Files saved in {output_dir}/")

    def create_cnxi(self, js_fd=None):
        """Create all compounds with the cylcic symmetry.

        The self.no_of specifies for which n in n-fold symmetry axis to generated models.
        """
        # example rotation
        for i in self.no_of:
            # n | CnxI  / ExI
            # with n >= 2
            n = i + 1
            axis_eg = geomtypes.Vec3([1, 2, 3])
            polyh = S4xI.CnxI_ExI(self.descr, n, n, axis=axis_eg)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            base_rot = geomtypes.Rot3(axis=axis_eg, angle=math.pi / 6)
            polyh.transform_base(base_rot)
            save_off(polyh)

    def create_dnxi(self, js_fd=None):
        """Create all compounds with the dihedral symmetry.

        The self.no_of specifies for which n-fold symmetry axis.
        """
        # example rotation
        for i in self.no_of:
            # 2n | DnxI  / ExI
            # with n >= 1
            n = i
            axis_eg = geomtypes.Vec3([1, 2, 3])
            polyh = S4xI.DnxI_ExI(self.descr, n, n, axis=axis_eg)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            base_rot = geomtypes.Rot3(axis=axis_eg, angle=math.pi / (2 * i))
            polyh.transform_base(base_rot)
            save_off(polyh)

        # Rotation freedom (around 1 axis)
        for i in self.no_of:
            # nA | DnxI  / C2xI
            # with n >= 3
            n = i + 2
            polyh = S4xI.DnxI_C2xI_A(self.descr, n, n)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            polyh.rot_base(math.pi / 6)  # example angle
            save_off(polyh)
            # special mu
            # mu_3: for n = 4, 6, 8 etc
            n, no_col = 2 + 2 * i, i + 1
            polyh = S4xI.DnxI_C2xI_A(self.descr, n, no_col)
            polyh.rot_base(polyh.mu[3])
            save_off(polyh, "_mu3")
            # mu_4: for n = 4, 6, 8 etc (same as mu_3)
            polyh = S4xI.DnxI_C2xI_A(self.descr, n, no_col)
            polyh.rot_base(polyh.mu[4])
            save_off(polyh, "_mu4")
            # mu_5: for n = 5, 6, 7 etc (same as mu_3)
            n, no_col = 4 * i, i
            polyh = S4xI.DnxI_C2xI_A(self.descr, n, no_col)
            polyh.rot_base(polyh.mu[5])
            save_off(polyh, "_mu5")

            # nB | DnxI  / C2xI
            # with n >= 3
            n = i + 2
            polyh = S4xI.DnxI_C2xI_B(self.descr, n, n)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            polyh.rot_base(math.pi / 6)  # example angle
            save_off(polyh)
            # special mu
            # mu_2: for n = 4, 6, 8,..
            n, no_col = 2 + 2 * i, i + 1
            polyh = S4xI.DnxI_C2xI_B(self.descr, n, no_col)
            polyh.rot_base(polyh.mu[2])
            save_off(polyh, "_mu2")
            # mu_3: for n = 3, 6, 9,..
            n, no_col = 3 * i, i
            n, no_col = (n, n // 3) if n % 3 == 0 else (3 * n, n)
            polyh = S4xI.DnxI_C2xI_B(self.descr, n, no_col)
            polyh.rot_base(polyh.mu[3])
            save_off(polyh, "_mu3")
            # mu_4: for n = 5, 10, 15,..
            n, no_col = 5 * i, i
            polyh = S4xI.DnxI_C2xI_B(self.descr, n, no_col)
            polyh.rot_base(polyh.mu[4])
            save_off(polyh, "_mu4")

            # m | DmxI  / D1xI, with m = 2n, n >= 1
            n = 2 * i
            no_col = n if n == 2 else i
            polyh = S4xI.DnxI_D1xI(self.descr, n, no_col)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            polyh.rot_base(math.pi / (3 * n / 2))  # example angle
            save_off(polyh)
            # mu_3: for n = 2, 4, 6
            n = 2 * i
            no_col = n if n == 2 else i
            polyh = S4xI.DnxI_D1xI(self.descr, n, no_col)
            polyh.rot_base(polyh.mu[2])
            save_off(polyh, "_mu2")

            # 2n | D3nxI  / C3xI
            # with n >= 1
            n = i
            no_col = 2 if n == 1 else n
            polyh = S4xI.D3nxI_C3xI(self.descr, n, no_col)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            polyh.rot_base(polyh.mu[1] / 2)  # example angle
            save_off(polyh)

            # 2n | D4nxI  / C4xI
            # with n >= 1
            n = i
            no_col = 2 if n == 1 else n
            polyh = S4xI.D4nxI_C4xI(self.descr, n, no_col)
            if js_fd is not None:
                js_fd.write(polyh.to_js())
            polyh.write_json_file(get_stem(polyh) + ".json")
            polyh.rot_base(polyh.mu[1] / 2)  # example angle
            save_off(polyh)

            # Rigid compounds
            n = i + 1
            no_col = n if n % 2 == 1 or n == 2 else n // 2
            polyh = S4xI.D4nxI_D4xI(self.descr, n, no_col)
            save_off(polyh)

            polyh = S4xI.D3nxI_D3xI(self.descr, n, no_col)
            save_off(polyh)

            polyh = S4xI.D2nxI_D2xI(self.descr, n, no_col)
            save_off(polyh)

    def create_a4xi(self, js_fd=None):
        """Create all compounds with the symmetry of a tetrahedron and a cetral inversion."""
        # example rotation
        polyh = S4xI.A4xI_ExI(self.descr, 4, col_alt=2)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 3]), angle=math.pi / 6)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        polyh = S4xI.A4xI_C2xI(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        polyh.rot_base(math.pi / 6)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.A4xI_C2xI(self.descr, 3)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

        polyh = S4xI.A4xI_C3xI(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        polyh.rot_base(5 * math.pi / 18)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.A4xI_C3xI(self.descr, 4)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")

    def create_s4xi(self, js_fd=None):
        """Create all compounds with the complete symmetry of a cube."""
        polyh = S4xI.S4xI_ExI(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        # example rotation
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([2, 1, 0]), angle=math.pi / 2)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        polyh = S4xI.S4xI_C2xI_A(self.descr, 4)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
        polyh.rot_base(2 * math.pi / 9)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.S4xI_C3xI(self.descr, 4)
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2")
        polyh = S4xI.S4xI_C3xI(
            self.descr,
            8,
            cols=[
                S4xI.S4xI_C3xI.cols[0],
                S4xI.S4xI_C3xI.cols[0],
                S4xI.S4xI_C3xI.cols[1],
                S4xI.S4xI_C3xI.cols[2],
                S4xI.S4xI_C3xI.cols[3],
                S4xI.S4xI_C3xI.cols[2],
                S4xI.S4xI_C3xI.cols[3],
                S4xI.S4xI_C3xI.cols[1],
            ],
        )
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2.alt1")
        polyh = S4xI.S4xI_C3xI(
            self.descr,
            8,
            cols=[
                S4xI.S4xI_C3xI.cols[0],
                S4xI.S4xI_C3xI.cols[1],
                S4xI.S4xI_C3xI.cols[2],
                S4xI.S4xI_C3xI.cols[2],
                S4xI.S4xI_C3xI.cols[1],
                S4xI.S4xI_C3xI.cols[3],
                S4xI.S4xI_C3xI.cols[0],
                S4xI.S4xI_C3xI.cols[3],
            ],
        )
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2.alt2")
        polyh = S4xI.S4xI_C3xI(
            self.descr,
            8,
            cols=[
                S4xI.S4xI_C3xI.cols[0],
                S4xI.S4xI_C3xI.cols[1],
                S4xI.S4xI_C3xI.cols[2],
                S4xI.S4xI_C3xI.cols[3],
                S4xI.S4xI_C3xI.cols[0],
                S4xI.S4xI_C3xI.cols[2],
                S4xI.S4xI_C3xI.cols[1],
                S4xI.S4xI_C3xI.cols[3],
            ],
        )
        polyh.rot_base(polyh.mu[2])
        save_off(polyh, "_mu2.alt3")
        polyh = S4xI.S4xI_C3xI(self.descr, 4)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3")

        polyh = S4xI.S4xI_C4xI(self.descr, 3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh = S4xI.A5xI_ExI(self.descr, 12, col_alt=3)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
        base_rot = geomtypes.Rot3(axis=geomtypes.Vec3([1, 2, 0]), angle=math.pi / 9)
        polyh.transform_base(base_rot)
        save_off(polyh)

        # Rotation freedom (around 1 axis)
        # 30A | A5 x I / C2 x I
        #######################################
        polyh = S4xI.A5xI_C2xI_A(self.descr, 6)
        if js_fd is not None:
            js_fd.write(polyh.to_js())
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
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
        polyh.write_json_file(get_stem(polyh) + ".json")
        polyh.rot_base(math.pi / 7)  # example angle
        save_off(polyh)
        # special mu
        polyh = S4xI.A5xI_C3xI(self.descr, 5)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3.1")
        polyh = S4xI.A5xI_C3xI(self.descr, 5, col_alt=1)
        polyh.rot_base(polyh.mu[3])
        save_off(polyh, "_mu3.2")
        polyh = S4xI.A5xI_C3xI(self.descr, 5)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4.1")
        polyh = S4xI.A5xI_C3xI(self.descr, 5, col_alt=1)
        polyh.rot_base(polyh.mu[4])
        save_off(polyh, "_mu4.2")
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
