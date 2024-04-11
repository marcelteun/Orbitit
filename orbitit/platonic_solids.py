#!/usr/bin/env python3
"""Classes defining the 5 Platonic "solids"."""

# Copyright (C) 2022-2024 Marcel Tunnissen
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
# pylint: disable=too-few-public-methods
# Ignore duplicate code with archimedean_solids
# pylint: disable=duplicate-code
from math import sqrt as V

from orbitit.base import add_std_arguments_for_generating_models
from orbitit.geom_3d import A5_Z_O2_TO_O3, A5_Z_O2_TO_O5, A4_Z_O2_TO_O3, S4_Z_O4_TO_O2
from orbitit.geomtypes import Vec3
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
        "vs": [
            Vec3([1, -1, 1]),
            Vec3([1, 1, -1]),
            Vec3([-1, 1, 1]),
        ],
        "fs": [[0, 1, 2]],
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

class TetrahedronZO3(Tetrahedron):
    """Model of tetrahedron where the z-axis is shared with a 3-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(A4_Z_O2_TO_O3)
        self.name = "tetrahedron_z_o3"

#------------------------------------------------------------------------------
# Cube
class Cube(OrbitShape):
    """Model of cube."""
    base = {
        "vs": [
            Vec3([1, 1, 1]),
            Vec3([-1, 1, 1]),
            Vec3([-1, -1, 1]),
            Vec3([1, -1, 1]),
        ],
        "fs": [[0, 1, 2, 3]],
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

class CubeZO3(Cube):
    """Model of cube where the z-axis is shared with a 3-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(A4_Z_O2_TO_O3)
        self.name = "cube_z_o3"

class CubeZO2(Cube):
    """Model of cube where the z-axis is shared with a 2-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(S4_Z_O4_TO_O2)
        self.name = "cube_z_o2"

#------------------------------------------------------------------------------
# Octahedron
class Octahedron(OrbitShape):
    """Model of octahedron."""
    base = {
        "vs": [
            Vec3([0, 0, 1]),
            Vec3([1, 0, 0]),
            Vec3([0, 1, 0]),
        ],
        "fs": [[0, 1, 2]],
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

class OctahedronZO3(Octahedron):
    """Model of octahedron where the z-axis is shared with a 3-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(A4_Z_O2_TO_O3)
        self.name = "octahedron_z_o3"

class OctahedronZO2(Octahedron):
    """Model of octahedron where the z-axis is shared with a 2-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(S4_Z_O4_TO_O2)
        self.name = "octahedron_z_o2"

#------------------------------------------------------------------------------
# Dodecahedron
class Dodecahedron(OrbitShape):
    """Model of dodecahedron."""
    base = {
        "vs": [
            Vec3([0, -1, TAU + 1]),
            Vec3([TAU, -TAU, TAU]),
            Vec3([TAU + 1, 0, 1]),
            Vec3([TAU, TAU, TAU]),
            Vec3([0, 1, TAU + 1]),
        ],
        "fs": [[0, 1, 2, 3, 4]],
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

class DodecahedronZO3(Dodecahedron):
    """Model of dodecahedron where the z-axis is shared with a 3-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(A5_Z_O2_TO_O3)
        self.name = "dodecahedron_z_o3"

class DodecahedronZO5(Dodecahedron):
    """Model of dodecahedron where the z-axis is shared with a 3-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(A5_Z_O2_TO_O5)
        self.name = "dodecahedron_z_o5"

#------------------------------------------------------------------------------
# Icosahedron
class Icosahedron(OrbitShape):
    """Model of icosahedron."""
    base = {
        "vs": [
            Vec3([1, 0, TAU]),
            Vec3([TAU, 1, 0]),
            Vec3([0, TAU, 1]),
        ],
        "fs": [[0, 1, 2]],
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

class IcosahedronZO3(Icosahedron):
    """Model of icosahedron where the z-axis is shared with a 3-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(A5_Z_O2_TO_O3)
        self.name = "icosahedron_z_o3"

class IcosahedronZO5(Icosahedron):
    """Model of icosahedron where the z-axis is shared with a 5-fold axis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transform(A5_Z_O2_TO_O5)
        self.name = "icosahedron_z_o5"

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path
    from orbitit import geomtypes

    def shape_to_filename(shape):
        """Create a suitable filename from shape.name."""
        return Path(f"{shape.name}.json")

    MODELS_MAP = {
        "tetrahedron": Tetrahedron(),
        "tetrahedron_z_o3": TetrahedronZO3(),
        "cube": Cube(),
        "cube_z_o3": CubeZO3(),
        "cube_z_o2": CubeZO2(),
        "octahedron": Octahedron(),
        "octahedron_z_o3": OctahedronZO3(),
        "octahedron_z_o2": OctahedronZO2(),
        "dodecahedron": Dodecahedron(),
        "dodecahedron_z_o3": DodecahedronZO3(),
        "dodecahedron_z_o5": DodecahedronZO5(),
        "icosahedron": Icosahedron(),
        "icosahedron_z_o3": IcosahedronZO3(),
        "icosahedron_z_o5": IcosahedronZO5(),
    }

    PARSER = ArgumentParser(DESCR)
    add_std_arguments_for_generating_models(PARSER, list(MODELS_MAP.keys()))
    ARGS = PARSER.parse_args()
    OUT_DIR = Path(ARGS.out_dir)

    # TODO: share even more code. Perhaps make a class
    if ARGS.out_dir:
        OUT_DIR = Path(ARGS.out_dir)
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
                FILENAME = ARGS.out_dir / shape_to_filename(model_shape)
                if ARGS.indent:
                    model_shape.json_indent = ARGS.indent
                model_shape.write_json_file(FILENAME)
                print(f"written {FILENAME}")
        FILENAME = model.name.lower().replace(" ", "_")
        if ARGS.json:
            FILENAME = OUT_DIR / Path(FILENAME + ".json")
            if ARGS.indent:
                model.json_indent = ARGS.indent
            model.write_json_file(FILENAME)
        else:
            FILENAME = OUT_DIR / Path(FILENAME + ".off")
            with open(FILENAME, "w") as fd:
                model.clean_shape(geomtypes.FLOAT_PRECISION)
                fd.write(model.to_off(precision=geomtypes.float_out_precision))
        print(f"written {FILENAME}")
