#!/usr/bin/env python3
"""Classes defining the 13 Archimedean polyhedra."""
from orbitit.Geom3D import CompoundShape
from orbitit.geomtypes import Vec3
from math import sqrt as V
from orbitit import isometry as sym
from orbitit.orbit import Shape
import re

V5 = V(5)
τ = (V5 + 1) / 2

# related to the snub cube
δ_ = 3*V(33)
t = (19 + δ_)**(1/3)
t += (19 - δ_)**(1/3)
t += 1
t /= 3

# related to snub dodecahedron:
δ_ = V(τ - 5/27)
ξ = ((τ + δ_) / 2)**(1/3)
ξ += ((τ - δ_) / 2)**(1/3)
α = ξ - 1 / ξ
β = τ * (ξ + τ) + τ / ξ

S4_O3 = {"axis": Vec3([1, 1, 1])}

A5_O3 = {"axis": Vec3([1, 1, 1])}
A5_O5 = {"axis": Vec3([1, 0, τ])}

def shape_to_filename(shape):
    name, polygon, sym = re.split("[{}]", shape.name)
    name = name.strip().lower()
    name = name.replace(" ", "_")
    polygon = polygon.strip().replace("/", "_")
    sym = re.sub(" */ *", "_", sym.strip())
    return f"{name}_bas_{polygon}_{sym}.json"

#------------------------------------------------------------------------------
# The Archimedean solids in alphabetical order
#------------------------------------------------------------------------------

class SnubCube_3_S4_C3(Shape):
    """The 8 triangles of the snub cube sharing a 3-fold axis."""
    base = {
        "Vs": [
            Vec3([1, 1 / t, t]),
            Vec3([t, 1, 1 / t]),
            Vec3([1 / t, t, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C3(setup=S4_O3),
            name="Snub Cube {3} S4 / C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class SnubCube_3_S4_E(Shape):
    """The 24 triangles of the snub cube not sharing a symmetry."""
    base = {
        "Vs": [
            Vec3([-1 / t, 1, t]),
            Vec3([1, 1 / t, t]),
            Vec3([1 / t, t, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.E(),
            name="Snub Cube {3} S4 / E",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class SnubCube_4_S4_C4(Shape):
    """The 6 squares of the snub cube."""
    base = {
        "Vs": [
            Vec3([1, 1 / t, t]),
            Vec3([-1 / t, 1, t]),
            Vec3([-1, -1 / t, t]),
            Vec3([1 / t, -1, t]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C4(),
            name="Snub Cube {4} S4 / C4",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class SnubCube(CompoundShape):
    def __init__(self):
        super().__init__(
            [
                SnubCube_3_S4_C3(cols=[Shape.cols[0]]),
                SnubCube_3_S4_E(cols=[Shape.cols[1]]),
                SnubCube_4_S4_C4(cols=[Shape.cols[2]]),
            ],
            name="snub cube",
        )

class SnubDodecahedron_3_A5_E(Shape):
    """The 60 triangles of the snub dodecahedron not sharing a symmetry."""
    base = {
        "Vs": [
            Vec3([2 * α, -2, 2 * β]),
            Vec3([α + β / τ - τ, -α * τ + β - 1 / τ, α / τ + β * τ + 1]),
            Vec3([-2 * α, 2, 2 * β]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.E(),
            name="Snub Dodecahedron {3} A5 / E",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class SnubDodecahedron_3_A5_C3(Shape):
    """The 20 triangles of the snub dodecahedron sharing a 3-fold axis."""
    base = {
        "Vs": [
            Vec3([-α / τ + β * τ - 1, -α + β / τ + τ, α * τ + β + 1 / τ]),
            Vec3([α * τ + β + 1 / τ, -α / τ + β * τ - 1, -α + β / τ + τ]),
            Vec3([-α + β / τ + τ, α * τ + β + 1 / τ, -α / τ + β * τ - 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C3(setup=A5_O3),
            name="Snub Dodecahedron {3} A5 / C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class SnubDodecahedron_5_A5_C5(Shape):
    """The 12 pentagons of the snub dodecahedron."""
    base = {
        "Vs": [
            Vec3([α + β / τ - τ, -α * τ + β - 1 / τ, α / τ + β * τ + 1]),
            Vec3([2 * α, -2, 2 * β]),
            Vec3([α + β / τ + τ, α * τ - β - 1 / τ, α / τ + β * τ - 1]),
            Vec3([-α / τ + β * τ + 1,  + α - β / τ + τ, α * τ + β - 1 / τ]),
            Vec3([-α / τ + β * τ - 1, -α + β / τ + τ, α * τ + β + 1 / τ]),
        ],
        "Fs": [[0, 1, 2, 3, 4]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C5(setup=A5_O5),
            name="Snub Dodecahedron {5} A5 / C5",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class SnubDodecahedron(CompoundShape):
    def __init__(self):
        super().__init__(
            [
                SnubDodecahedron_5_A5_C5(cols=[Shape.cols[0]]),
                SnubDodecahedron_3_A5_E(cols=[Shape.cols[1]]),
                SnubDodecahedron_3_A5_C3(cols=[Shape.cols[2]]),
            ],
            name="snub dodecahedron",
        )

if __name__ == "__main__":
    import argparse

    models = [
        SnubCube(),
        SnubDodecahedron(),
    ]
    for model in models:
        for shape in model.shapes:
            filename = shape_to_filename(shape)
            shape.write_json_file(filename)
            print(f"written {filename}")
        filename = model.name.lower().replace(" ", "_") + ".off"
        with open(filename, "w") as fd:
            fd.write(model.to_off())
            print(f"written {filename}")
