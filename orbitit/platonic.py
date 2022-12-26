#!/usr/bin/env python3
"""Classes defining the 5 Platonic "solids"."""

# Copyright (C) 2022 Marcel Tunnissen
#
# License: GNU Public License version 2
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not,
# check at http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# or write to the Free Software Foundation,
# ------------------------------------------------------------------
from math import sqrt as V

from orbitit.geomtypes import Vec3
from orbitit.geom_3d import SimpleShape
from orbitit import isometry as sym
from orbitit.orbit import Shape as OrbitShape

DESCR = """Generate SW models for the Platonic solids.

One can choose to generate all or just one and which file format. If no argument is given all models
will be generated in the OFF format.
"""

V5 = V(5)
TAU = (V5 + 1) / 2

A4_O3 = {"axis": Vec3([1, 1, 1])}

S4_O3 = {"axis": Vec3([1, 1, 1])}

A5_O3 = {"axis": Vec3([1, 1, 1])}
A5_O5 = {"axis": Vec3([1, 0, TAU])}

#------------------------------------------------------------------------------
# The Archimedean order according to the amount of faces
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Tetrehedron
class Tetrahedron(OrbitShape):
    """Model of tetrahedron."""
    base = {
        "Vs": [
            Vec3([1, -1, 1]),
            Vec3([1, 1, -1]),
            Vec3([-1, 1, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=4, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A4(),
            stab_sym=sym.C3(setup=A4_O3),
            name="tetrahedron",
            no_of_cols=no_of_cols,
            **kwargs,
        )

#------------------------------------------------------------------------------
# Cube
class Cube(OrbitShape):
    """Model of cube."""
    base = {
        "Vs": [
            Vec3([1, 1, 1]),
            Vec3([-1, 1, 1]),
            Vec3([-1, -1, 1]),
            Vec3([1, -1, 1]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=3, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C4(),
            name="cube",
            no_of_cols=no_of_cols,
            **kwargs,
        )

#------------------------------------------------------------------------------
# Octahedron
class Octahedron(OrbitShape):
    """Model of octahedron."""
    base = {
        "Vs": [
            Vec3([0, 0, 1]),
            Vec3([1, 0, 0]),
            Vec3([0, 1, 0]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=2, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C3(setup=S4_O3),
            name="octahedron",
            no_of_cols=no_of_cols,
            **kwargs,
        )

#------------------------------------------------------------------------------
# Dodecahedron
class Dodecahedron(OrbitShape):
    """Model of dodecahedron."""
    base = {
        "Vs": [
            Vec3([0, -1, TAU + 1]),
            Vec3([TAU, -TAU, TAU]),
            Vec3([TAU + 1, 0, 1]),
            Vec3([TAU, TAU, TAU]),
            Vec3([0, 1, TAU + 1]),
        ],
        "Fs": [[0, 1, 2, 3, 4]],
    }
    def __init__(self, no_of_cols=6, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C5(setup=A5_O5),
            name="dodecahedron",
            no_of_cols=no_of_cols,
            **kwargs,
        )

#------------------------------------------------------------------------------
# Icosahedron
class Icosahedron(OrbitShape):
    """Model of icosahedron."""
    base = {
        "Vs": [
            Vec3([1, 0, TAU]),
            Vec3([TAU, 1, 0]),
            Vec3([0, TAU, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=5, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C3(setup=A5_O3),
            name="icosahedron",
            no_of_cols=no_of_cols,
            **kwargs,
        )

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path
    from orbitit import geomtypes

    def shape_to_filename(shape):
        """Create a suitable filename from shape.name."""
        return Path(f"{shape.name}.json")

    MODELS_MAP = {
        "tetrahedron": Tetrahedron(),
        "cube": Cube(),
        "octahedron": Octahedron(),
        "dodecahedron": Dodecahedron(),
        "icosahedron": Icosahedron(),
    }

    PARSER = ArgumentParser(DESCR)
    PARSER.add_argument(
        "--indent", "-i",
        metavar="NO-OF-SPACES",
        type=int,
        help="When using JSON format indent each line with the specified number of spaces to make "
        "it human readable. Note that the file size might increase significantly.",
    )
    PARSER.add_argument(
        "--models", "-m",
        metavar="NAME",
        nargs="*",
        help=f"Specifiy which model(s) to generate. Specify one of {list(MODELS_MAP.keys())}. If "
        "nothing is specified all of them will be generated."
    )
    PARSER.add_argument(
        "--out-dir", "-o",
        default="",
        metavar="DIR",
        help="Specify possible output directory. Should exist.",
    )
    PARSER.add_argument(
        "--precision", "-p",
        metavar="NO-OF-DIGITS",
        type=int,
        help="Specify number of decimals to use when saving files. Negative numbers are ignored",
    )
    PARSER.add_argument(
        "--seperate-orbits", "-s",
        action='store_true',
        help="Also save the seperate parts consisting of one kind of polygon described by one "
        "orbit. This is always saved in JSON.",
    )
    PARSER.add_argument(
        "--json", "-j",
        action='store_true',
        help="Save the complete polyhedron in JSON format (default OFF)",
    )
    ARGS = PARSER.parse_args()
    OUT_DIR = Path(ARGS.out_dir)

    if ARGS.out_dir:
        OUT_DIR = Path(ARGS.OUT_DIR)
        if not OUT_DIR.is_dir():
            raise ValueError(f"The path '{ARGS.out_dir}' doesn't exist")
    else:
        OUT_DIR = Path("")

    if ARGS.precision and ARGS.precision > 0:
        geomtypes.float_out_precision = ARGS.precision

    if ARGS.models:
        MODELS = [MODELS_MAP[name] for name in ARGS.models]
    else:
        MODELS = list(MODELS_MAP.values())
    for model in MODELS:
        if ARGS.seperate_orbits:
            for model_shape in model.shapes:
                filename = OUT_DIR / shape_to_filename(model_shape)
                if ARGS.indent:
                    model_shape.json_indent = ARGS.indent
                model_shape.write_json_file(filename)
                print(f"written {filename}")
        filename = model.name.lower().replace(" ", "_")
        if ARGS.json:
            filename = OUT_DIR / Path(filename + ".json")
            if ARGS.indent:
                model.json_indent = ARGS.indent
            model.write_json_file(filename)
        else:
            filename = OUT_DIR / Path(filename + ".off")
            with open(filename, "w") as fd:
                model.clean_shape(geomtypes.FLOAT_PRECISION)
                fd.write(model.to_off(precision=geomtypes.float_out_precision))
        print(f"written {filename}")
