#!/usr/bin/env python3
"""Classes defining the 13 Archimedean polyhedra."""
from orbitit.Geom3D import CompoundShape
from orbitit.geomtypes import Vec3
from math import sqrt as V
from orbitit import isometry as sym
from orbitit.orbit import Shape
import re

V2 = V(2)
V5 = V(5)
τ = (V5 + 1) / 2

γ = V2 - 1
ω = V2 + 1

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

A4_O3 = {"axis": Vec3([1, 1, 1])}

S4_O2 = {"axis": Vec3([0, 1, 1])}
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

#------------------------------------------------------------------------------
# Cuboctahedron
class Cuboctahedron_3_S4xI_D3C3(Shape):
    """The 8 triangles of the cuboctahedron."""
    base = {
        "Vs": [
            Vec3([1, 0, 1]),
            Vec3([1, 1, 0]),
            Vec3([0, 1, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C3(setup=S4_O3),
            name="Cuboctahedron {3} S4xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Cuboctahedron_4_S4xI_D4C4(Shape):
    """The 6 squares of the cuboctahedron."""
    base = {
        "Vs": [
            Vec3([1, 0, 1]),
            Vec3([0, 1, 1]),
            Vec3([-1, 0, 1]),
            Vec3([0, -1, 1]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C4(),
            name="Cuboctahedron {4} S4xI / D4C4",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Cuboctahedron(CompoundShape):
    def __init__(self):
        super().__init__(
            [
                Cuboctahedron_3_S4xI_D3C3(cols=[Shape.cols[0]]),
                Cuboctahedron_4_S4xI_D4C4(cols=[Shape.cols[1]]),
            ],
            name="cuboctahedron",
        )

#------------------------------------------------------------------------------
# Rhombicuboctahedron
class Rhombicuboctahedron_3_S4xI_D3C3(Shape):
    """The 8 triangles of the rhombicuboctahedron."""
    base = {
        "Vs": [
            Vec3([1, 1, ω]),
            Vec3([ω, 1, 1]),
            Vec3([1, ω, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C3(setup=S4_O3),
            name="Rhombicuboctahedron {3} S4xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Rhombicuboctahedron_4_S4xI_D2C2(Shape):
    """The 12 squares of the rhombicuboctahedron sharing a 2-fold axis."""
    base = {
        "Vs": [
            Vec3([1, 1, ω]),
            Vec3([1, ω, 1]),
            Vec3([-1, ω, 1]),
            Vec3([-1, 1, ω]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C2(setup=S4_O2),
            name="Rhombicuboctahedron {4} S4xI / D2C2",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Rhombicuboctahedron_4_S4xI_D4C4(Shape):
    """The 6 squares of the rhombicuboctahedron sharing a 4-fold axis."""
    base = {
        "Vs": [
            Vec3([1, 1, ω]),
            Vec3([-1, 1, ω]),
            Vec3([-1, -1, ω]),
            Vec3([1, -1, ω]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C4(),
            name="Rhombicuboctahedron {4} S4xI / D4C4",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Rhombicuboctahedron(CompoundShape):
    def __init__(self):
        super().__init__(
            [
                Rhombicuboctahedron_3_S4xI_D3C3(cols=[Shape.cols[0]]),
                Rhombicuboctahedron_4_S4xI_D2C2(cols=[Shape.cols[1]]),
                Rhombicuboctahedron_4_S4xI_D4C4(cols=[Shape.cols[2]]),
            ],
            name="rhombicuboctahedron",
        )

#------------------------------------------------------------------------------
# Snub Cube
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

#------------------------------------------------------------------------------
# Snub Dodecahedron
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

#------------------------------------------------------------------------------
# Truncated Cube
class TruncatedCube_3_S4xI_D3C3(Shape):
    """The 8 triangles of the truncated cube."""
    base = {
        "Vs": [
            Vec3([1, γ, 1]),
            Vec3([1, 1, γ]),
            Vec3([γ, 1, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C3(setup=S4_O3),
            name="Truncated cube {3} S4xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedCube_8_S4xI_D4C4(Shape):
    """The 8 octagons of the truncated cube."""
    base = {
        "Vs": [
            Vec3([1, γ, 1]),
            Vec3([γ, 1, 1]),
            Vec3([-γ, 1, 1]),
            Vec3([-1, γ, 1]),
            Vec3([-1, -γ, 1]),
            Vec3([-γ, -1, 1]),
            Vec3([γ, -1, 1]),
            Vec3([1, -γ, 1]),
        ],
        "Fs": [[0, 1, 2, 3, 4, 5, 6, 7]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C4(),
            name="Truncated cube {8} S4xI / D4C4",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedCube(CompoundShape):
    def __init__(self):
        super().__init__(
            [
                TruncatedCube_3_S4xI_D3C3(cols=[Shape.cols[0]]),
                TruncatedCube_8_S4xI_D4C4(cols=[Shape.cols[1]]),
            ],
            name="truncated cube",
        )

#------------------------------------------------------------------------------
# Truncated Octahedron
class TruncatedOctahedron_6_S4xI_D3C3(Shape):
    """The 8 hexahedron of the truncated cube."""
    base = {
        "Vs": [
            Vec3([1, 0, 2]),
            Vec3([2, 0, 1]),
            Vec3([2, 1, 0]),
            Vec3([1, 2, 0]),
            Vec3([0, 2, 1]),
            Vec3([0, 1, 2]),
        ],
        "Fs": [[0, 1, 2, 3, 4, 5]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C3(setup=S4_O3),
            name="Truncated octahedron {6} S4xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedOctahedron_4_S4xI_D4C4(Shape):
    """The 8 octagons of the truncated cube."""
    base = {
        "Vs": [
            Vec3([1, 0, 2]),
            Vec3([0, 1, 2]),
            Vec3([-1, 0, 2]),
            Vec3([0, -1, 2]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C4(),
            name="Truncated octahedron {4} S4xI / D4C4",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedOctahedron(CompoundShape):
    def __init__(self):
        super().__init__(
            [
                TruncatedOctahedron_6_S4xI_D3C3(cols=[Shape.cols[0]]),
                TruncatedOctahedron_4_S4xI_D4C4(cols=[Shape.cols[1]]),
            ],
            name="truncated octahedron",
        )

#------------------------------------------------------------------------------
# Truncated Tetrahedron
class TruncatedTetrahedron_3_S4A4_D3C3(Shape):
    """The 4 triangles of the truncated tetrahedron."""
    base = {
        "Vs": [
            Vec3([1, 1, 3]),
            Vec3([3, 1, 1]),
            Vec3([1, 3, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A4(),
            stab_sym=sym.C3(setup=A4_O3),
            name="Truncated tetrahedron {3} S4A4 / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedTetrahedron_6_S4A4_D3C3(Shape):
    """The 6 hexagons of the truncated tetrahedron."""
    base = {
        "Vs": [
            Vec3([1, 1, 3]),
            Vec3([1, 3, 1]),
            Vec3([-1, 3, -1]),
            Vec3([-3, 1, -1]),
            Vec3([-3, -1, 1]),
            Vec3([-1, -1, 3]),
        ],
        "Fs": [[0, 1, 2, 3, 4, 5]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A4(),
            stab_sym=sym.C3(setup={"axis": Vec3([-1, 1, 1])}),
            name="Truncated tetrahedron {6} S4A4 / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedTetrahedron(CompoundShape):
    def __init__(self):
        super().__init__(
            [
                TruncatedTetrahedron_3_S4A4_D3C3(cols=[Shape.cols[0]]),
                TruncatedTetrahedron_6_S4A4_D3C3(cols=[Shape.cols[1]]),
            ],
            name="truncated tetrahedron",
        )

if __name__ == "__main__":
    import argparse

    models = [
        Cuboctahedron(),
        Rhombicuboctahedron(),
        SnubCube(),
        SnubDodecahedron(),
        TruncatedCube(),
        TruncatedOctahedron(),
        TruncatedTetrahedron(),
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
