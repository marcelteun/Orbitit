#!/usr/bin/env python3
"""Classes defining the 13 Archimedean polyhedra."""

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
#
# The following is because of the class names. I keep the naming because the capitals are used in
# mathematics and theay are nest separated by _
# I also would like to keep the Greek variable names without using capitals.
# pylint: disable=invalid-name,too-many-lines
from math import sqrt as V
import re

from orbitit.Geom3D import CompoundShape
from orbitit.geomtypes import Vec3
from orbitit import isometry as sym
from orbitit.orbit import Shape

DESCR = """Generate SW models for Archimedean solids.

One can choose to generate all or just one and which file format. If no argument is given all models
will be generated in the OFF format.
"""

V2 = V(2)
V5 = V(5)
τ = (V5 + 1) / 2

γ = V2 - 1
ω = V2 + 1
ψ = ω + V2

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
    """Define a cuboctahedron."""
    def __init__(self):
        super().__init__(
            [
                Cuboctahedron_3_S4xI_D3C3(cols=[Shape.cols[0]]),
                Cuboctahedron_4_S4xI_D4C4(cols=[Shape.cols[1]]),
            ],
            name="cuboctahedron",
        )

#------------------------------------------------------------------------------
# Icosidodecahedron
class Icosidodecahedron_3_A5xI_D3C3(Shape):
    """The 20 triangles of the icosidodecahedron."""
    base = {
        "Vs": [
            Vec3([1, τ, τ + 1]),
            Vec3([τ + 1, 1, τ]),
            Vec3([τ, τ + 1, 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C3(setup=A5_O3),
            name="Icosidodecahedron {3} A5xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Icosidodecahedron_5_A5xI_D5C5(Shape):
    """The 12 pentagons of the icosidodecahedron."""
    base = {
        "Vs": [
            Vec3([0, 0, 2 * τ]),
            Vec3([1, -τ, τ + 1]),
            Vec3([τ + 1, -1, τ]),
            Vec3([τ + 1, 1, τ]),
            Vec3([1, τ, τ + 1]),
        ],
        "Fs": [[0, 1, 2, 3, 4]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C5(setup=A5_O5),
            name="Icosidodecahedron {5} A5xI / D5C5",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Icosidodecahedron(CompoundShape):
    """Define an icosidodecahedron."""
    def __init__(self):
        super().__init__(
            [
                Icosidodecahedron_3_A5xI_D3C3(cols=[Shape.cols[0]]),
                Icosidodecahedron_5_A5xI_D5C5(cols=[Shape.cols[1]]),
            ],
            name="icosidodecahedron",
        )

#------------------------------------------------------------------------------
# Rhombicosidodecahedron
class Rhombicosidodecahedron_5_A5xI_D5C5(Shape):
    """The 12 pentagons of the rhombicosidodecahedron"""
    base = {
        "Vs": [
            Vec3([1, -1, τ**3]),
            Vec3([τ + 1, -τ, 2 * τ]),
            Vec3([τ + 2, 0, τ + 1]),
            Vec3([τ + 1, τ, 2 * τ]),
            Vec3([1, 1, τ**3]),
        ],
        "Fs": [[0, 1, 2, 3, 4]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C5(setup=A5_O5),
            name="Rhombicosidodecahedron {5} A5xI / D5C5",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Rhombicosidodecahedron_3_A5xI_D3C3(Shape):
    """The 20 triangles of the rhombicosidodecahedron"""
    base = {
        "Vs": [
            Vec3([τ + 1, τ, 2 * τ]),
            Vec3([2 * τ, τ + 1, τ]),
            Vec3([τ, 2 * τ, τ + 1]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C3(setup=A5_O3),
            name="Rhombicosidodecahedron {3} A5xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Rhombicosidodecahedron_4_A5xI_D2C2(Shape):
    """The 30 squares of the rhombicosidodecahedron"""
    base = {
        "Vs": [
            Vec3([1, 1, τ**3]),
            Vec3([-1, 1, τ**3]),
            Vec3([-1, -1, τ**3]),
            Vec3([1, -1, τ**3]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C2(),
            name="Rhombicosidodecahedron {4} A5xI / D2C2",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class Rhombicosidodecahedron(CompoundShape):
    """Define a rhombicosidodecahedron."""
    def __init__(self):
        super().__init__(
            [
                Rhombicosidodecahedron_5_A5xI_D5C5(cols=[Shape.cols[0]]),
                Rhombicosidodecahedron_3_A5xI_D3C3(cols=[Shape.cols[1]]),
                Rhombicosidodecahedron_4_A5xI_D2C2(cols=[Shape.cols[2]]),
            ],
            name="rhombicosidodecahedron",
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
    """Define a rhombicuboctahedron."""
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
    """Define a sub cube."""
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
            Vec3([-α / τ + β * τ + 1, + α - β / τ + τ, α * τ + β - 1 / τ]),
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
    """Define a snub dodecahedron."""
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
    """Define a truncated cube."""
    def __init__(self):
        super().__init__(
            [
                TruncatedCube_3_S4xI_D3C3(cols=[Shape.cols[0]]),
                TruncatedCube_8_S4xI_D4C4(cols=[Shape.cols[1]]),
            ],
            name="truncated cube",
        )

#------------------------------------------------------------------------------
# Truncated Cuboctahedron
class TruncatedCuboctahedron_6_S4xI_D3C3(Shape):
    """The 8 hexagons of the truncated cuboctahedron."""
    base = {
        "Vs": [
            Vec3([ω, 1, ψ]),
            Vec3([ψ, 1, ω]),
            Vec3([ψ, ω, 1]),
            Vec3([ω, ψ, 1]),
            Vec3([1, ψ, ω]),
            Vec3([1, ω, ψ]),
        ],
        "Fs": [[0, 1, 2, 3, 4, 5]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C3(setup=S4_O3),
            name="Truncated cuboctahedron {6} S4xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedCuboctahedron_8_S4xI_D4C4(Shape):
    """The 6 octagons of the truncated cuboctahedron."""
    base = {
        "Vs": [
            Vec3([ω, 1, ψ]),
            Vec3([1, ω, ψ]),
            Vec3([-1, ω, ψ]),
            Vec3([-ω, 1, ψ]),
            Vec3([-ω, -1, ψ]),
            Vec3([-1, -ω, ψ]),
            Vec3([1, -ω, ψ]),
            Vec3([ω, -1, ψ]),
        ],
        "Fs": [[0, 1, 2, 3, 4, 5, 6, 7]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C4(),
            name="Truncated cuboctahedron {8} S4xI / D4C4",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedCuboctahedron_4_S4xI_D2C2(Shape):
    """The 12 squares of the truncated cuboctahedron."""
    base = {
        "Vs": [
            Vec3([1, ω, ψ]),
            Vec3([1, ψ, ω]),
            Vec3([-1, ψ, ω]),
            Vec3([-1, ω, ψ]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.S4(),
            stab_sym=sym.C2(setup=S4_O2),
            name="Truncated cuboctahedron {4} S4xI / D2C2",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedCuboctahedron(CompoundShape):
    """Define a truncated cuboctahedron."""
    def __init__(self):
        super().__init__(
            [
                TruncatedCuboctahedron_6_S4xI_D3C3(cols=[Shape.cols[0]]),
                TruncatedCuboctahedron_8_S4xI_D4C4(cols=[Shape.cols[1]]),
                TruncatedCuboctahedron_4_S4xI_D2C2(cols=[Shape.cols[2]]),
            ],
            name="truncated cuboctahedron",
        )

#------------------------------------------------------------------------------
# Truncated Dodecahedron
class TruncatedDodecahedron_3_A5xI_D3C3(Shape):
    """The 20 triangles of the truncated dodecahedron."""
    base = {
        "Vs": [
            Vec3([τ, 2, τ + 1]),
            Vec3([τ + 1, τ, 2]),
            Vec3([2, τ + 1, τ]),
        ],
        "Fs": [[0, 1, 2]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C3(setup=A5_O3),
            name="Truncated dodecahedron {3} A5xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedDodecahedron_10_A5xI_D5C5(Shape):
    """The 12 decagons of the truncated dodecahedron."""
    base = {
        "Vs": [
            Vec3([0, -τ + 1, τ + 2]),
            Vec3([τ - 1, -τ, 2 * τ]),
            Vec3([τ, -2, τ + 1]),
            Vec3([τ + 1, -τ, 2]),
            Vec3([2 * τ, -τ + 1, τ]),
            Vec3([2 * τ, τ - 1, τ]),
            Vec3([τ + 1, τ, 2]),
            Vec3([τ, 2, τ + 1]),
            Vec3([τ - 1, τ, 2 * τ]),
            Vec3([0, τ - 1, τ + 2]),

        ],
        "Fs": [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C5(setup=A5_O5),
            name="Truncated dodecahedron {10} A5xI / D5C5",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedDodecahedron(CompoundShape):
    """Define a truncated dodecahedron."""
    def __init__(self):
        super().__init__(
            [
                TruncatedDodecahedron_3_A5xI_D3C3(cols=[Shape.cols[0]]),
                TruncatedDodecahedron_10_A5xI_D5C5(cols=[Shape.cols[1]]),
            ],
            name="truncated dodecahedron",
        )

#------------------------------------------------------------------------------
# Truncated Icosahedron
class TruncatedIcosahedron_5_A5xI_D5C5(Shape):
    """The 12 pentagons of the truncated icosahedron."""
    base = {
        "Vs": [
            Vec3([1, 0, 3 * τ]),
            Vec3([2, -τ, 2 * τ + 1]),
            Vec3([τ + 2, -1, 2 * τ]),
            Vec3([τ + 2, 1, 2 * τ]),
            Vec3([2, τ, 2 * τ + 1]),
        ],
        "Fs": [[0, 1, 2, 3, 4]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C5(setup=A5_O5),
            name="Truncated icosahedron {5} A5xI / D5C5",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedIcosahedron_6_A5xI_D3C3(Shape):
    """The 20 hexagons of the truncated icosahedron."""
    base = {
        "Vs": [
            Vec3([2, τ, 2 * τ + 1]),
            Vec3([τ + 2, 1, 2 * τ]),
            Vec3([2 * τ + 1, 2, τ]),
            Vec3([2 * τ, τ + 2, 1]),
            Vec3([τ, 2 * τ + 1, 2]),
            Vec3([1, 2 * τ, τ + 2]),
        ],
        "Fs": [[0, 1, 2, 3, 4, 5]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C3(setup=A5_O3),
            name="Truncated icosahedron {6} A5xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedIcosahedron(CompoundShape):
    """Define a truncated icosahedron."""
    def __init__(self):
        super().__init__(
            [
                TruncatedIcosahedron_5_A5xI_D5C5(cols=[Shape.cols[0]]),
                TruncatedIcosahedron_6_A5xI_D3C3(cols=[Shape.cols[1]]),
            ],
            name="truncated icosahedron",
        )

#------------------------------------------------------------------------------
# Truncated Icosidodecahedron
class TruncatedIcosidodecahedron_10_A5xI_D5C5(Shape):
    """The 12 decagons of the truncated icosidodecahedron."""
    base = {
        "Vs": [
            Vec3([τ - 1, 1 - τ, τ + 3]),
            Vec3([2 / τ, -τ, 2 * τ + 1]),
            Vec3([2 * τ - 1, -2, τ + 2]),
            Vec3([2 * τ, -τ, 3]),
            Vec3([3 * τ - 1, 1 - τ, τ + 1]),
            Vec3([3 * τ - 1, τ - 1, τ + 1]),
            Vec3([2 * τ, τ, 3]),
            Vec3([2 * τ - 1, 2, τ + 2]),
            Vec3([2 / τ, τ, 2 * τ + 1]),
            Vec3([τ - 1, τ - 1, τ + 3]),
        ],
        "Fs": [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C5(setup=A5_O5),
            name="Truncated icosidodecahedron {10} A5xI / D5C5",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedIcosidodecahedron_6_A5xI_D3C3(Shape):
    """The 20 hexagons of the truncated icosidodecahedron."""
    base = {
        "Vs": [
            Vec3([2 * τ - 1, 2, τ + 2]),
            Vec3([2 * τ, τ, 3]),
            Vec3([τ + 2, 2 * τ - 1, 2]),
            Vec3([3, 2 * τ, τ]),
            Vec3([2, τ + 2, 2 * τ - 1]),
            Vec3([τ, 3, 2 * τ]),
        ],
        "Fs": [[0, 1, 2, 3, 4, 5]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C3(setup=A5_O3),
            name="Truncated icosidodecahedron {6} A5xI / D3C3",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedIcosidodecahedron_4_A5xI_D2C2(Shape):
    """The 30 squares of the truncated icosidodecahedron."""
    base = {
        "Vs": [
            Vec3([τ - 1, τ - 1, τ + 3]),
            Vec3([1 - τ, τ - 1, τ + 3]),
            Vec3([1 - τ, 1 - τ, τ + 3]),
            Vec3([τ - 1, 1 - τ, τ + 3]),
        ],
        "Fs": [[0, 1, 2, 3]],
    }
    def __init__(self, no_of_cols=1, **kwargs):
        super().__init__(
            self.base,
            final_sym=sym.A5(),
            stab_sym=sym.C2(),
            name="Truncated icosidodecahedron {4} A5xI / D2C2",
            no_of_cols=no_of_cols,
            **kwargs,
        )

class TruncatedIcosidodecahedron(CompoundShape):
    """Define a truncated icosidodecahedron."""
    def __init__(self):
        super().__init__(
            [
                TruncatedIcosidodecahedron_10_A5xI_D5C5(cols=[Shape.cols[0]]),
                TruncatedIcosidodecahedron_6_A5xI_D3C3(cols=[Shape.cols[1]]),
                TruncatedIcosidodecahedron_4_A5xI_D2C2(cols=[Shape.cols[2]]),
            ],
            name="truncated icosidodecahedron",
        )

#------------------------------------------------------------------------------
# Truncated Octahedron
class TruncatedOctahedron_6_S4xI_D3C3(Shape):
    """The 8 hexagons of the truncated cube."""
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
    """Define a truncated octahedron."""
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
    """Define a truncated tetrahedron."""
    def __init__(self):
        super().__init__(
            [
                TruncatedTetrahedron_3_S4A4_D3C3(cols=[Shape.cols[0]]),
                TruncatedTetrahedron_6_S4A4_D3C3(cols=[Shape.cols[1]]),
            ],
            name="truncated tetrahedron",
        )

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path

    parser = ArgumentParser(DESCR)
    parser.add_argument(
        "--out-dir", "-o",
        default="",
        metavar="DIR",
        help="Specify possible output directory. Should exist.",
    )
    parser.add_argument(
        "--seperate-orbits", "-s",
        action='store_true',
        help="Also save the seperate parts consisting of one kind of polygon described by one "
        "orbit. This is always saved in JSON.",
    )
    parser.add_argument(
        "--json", "-j",
        action='store_true',
        help="Save the complete polyhedron in JSON format (default OFF)",
    )
    args = parser.parse_args()
    out_dir = Path(args.out_dir)

    def shape_to_filename(shape):
        """Create a suitable filename from shape.name.

        This function assumes a certain naming; one that is used below and it will remove spaces and
        use lower case letter for the words, but not for the algebraic group names for the
        symmetries.
        """
        name, polygon, shape_sym = re.split("[{}]", shape.name)
        name = name.strip().lower()
        name = name.replace(" ", "_")
        polygon = polygon.strip().replace("/", "_")
        shape_sym = re.sub(" */ *", "_", shape_sym.strip())
        return Path(f"{name}_bas_{polygon}_{shape_sym}.json")

    if args.out_dir:
        out_dir = Path(args.out_dir)
        if not out_dir.is_dir():
            raise ValueError(f"The path '{args.out_dir}' doesn't exist")
    else:
        out_dir = Path("")

    MODELS = [
        Cuboctahedron(),
        Icosidodecahedron(),
        Rhombicosidodecahedron(),
        Rhombicuboctahedron(),
        SnubCube(),
        SnubDodecahedron(),
        TruncatedCube(),
        TruncatedCuboctahedron(),
        TruncatedDodecahedron(),
        TruncatedIcosahedron(),
        TruncatedIcosidodecahedron(),
        TruncatedOctahedron(),
        TruncatedTetrahedron(),
    ]
    for model in MODELS:
        if args.seperate_orbits:
            for model_shape in model.shapes:
                filename = out_dir / shape_to_filename(model_shape)
                model_shape.write_json_file(filename)
                print(f"written {filename}")
        filename = model.name.lower().replace(" ", "_")
        if args.json:
            filename = out_dir / Path(filename + ".json")
            model.write_json_file(filename)
        else:
            filename = out_dir / Path(filename + ".off")
            with open(filename, "w") as fd:
                fd.write(model.to_off())
        print(f"written {filename}")
