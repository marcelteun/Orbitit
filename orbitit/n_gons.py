#!/usr/bin/env python
"""
N-gons and n-gon based shapres

Like prisms and anti-prisms
"""
#
# Copyright (C) 2010-2026 Marcel Tunnissen
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
#
# ------------------------------------------------------------------
import logging
from math import cos, gcd, pi, sin, sqrt

from orbitit import geomtypes, geom_3d, isometry, orbit
from orbitit.colors import STD_COLORS as cols


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s - %(message)s",
    datefmt="%m-%d %H:%M",
)
LOGGER = logging.getLogger("pseudo copulaic prismatoid generator")
TWO_PI = 2 * pi
EDGE_LENGTH = 2


def get_polygon(
    n: int, m: int, edge_length: float = EDGE_LENGTH, height: float = 0, rotate: bool = True,
) -> list:
    """Return a list of polygons making a {n/m} polygon, each list containing vertices in 3D.

    The vertices are the vertices of an n-gon at z = 'height'. The edges of the n/m gram will
    scaled to edge_length.

    edge_length: the required edge length
    height: the z-coordinate.
    rotate: if this validates to True, then the first edge will be parallel to the Y-axis. Otherwise
        the first vertex will be on the x-axis.

    return: a list with vertices (geomtypes.Vec3)
    """
    # E.g. {7/2}
    #                           ^ X
    #              v4           |
    #       v1            v0    |
    #                           |
    #                           +
    #     v5                v3  |
    #                           |
    #                           |
    #          v2        v6     |
    # Y <-----------+-----------
    no_of_compounds = gcd(n, m)
    no_of_vs_x_gram = n // no_of_compounds
    if no_of_compounds > 1:
        LOGGER.info("{%i/%i} has a common divider", n, m)
    offset = m * pi / n if rotate else 0
    vs = [
        [
            geom_3d.vec(
                cos((m * i + j) * TWO_PI / n - offset),
                sin((m * i + j) * TWO_PI / n - offset),
                0,
            )
            for i in range(no_of_vs_x_gram)
        ]
        for j in range(no_of_compounds)
    ]

    diagonal = (vs[0][0] - vs[0][1]).norm()
    scale = edge_length / diagonal
    scaled = [[scale * v for v in v_list] for v_list in vs]
    if height:
        scaled = [[geom_3d.vec(v[0], v[1], height) for v in v_list] for v_list in scaled]
    return scaled


class AntiPrism(geom_3d.SimpleShape):
    """And {n/m} anti-prism."""

    def __init__(
        self,
        n: int,
        m: int = 1,
        edge_length: float = EDGE_LENGTH,
        use_outline: bool = False,
    ) -> geom_3d.SimpleShape:
        """Return a SimpleShape object that represents an anti-prism with {n/m} base.

        n: n in the {n/m} base
        m: n in the {n/m} base
        edge_length: the required edge length
        use_outline: set to False to use n sides for any {n/m}-gram where m > 1. For orbitit this
            will lead to holes for parts of the polygon that have double coverage. Using the outline
            lead to edges not really being shared between faces, since the {n/m}-gram will have 2n
            edges.
        """
        # Calculate height using law of cosines:
        # c^2 = a^2 + b^2 - 2ab.cos(γ)
        # --> (with a = b = r)
        # c^2 = 2r^2(1 - cos(2π/q)
        edge2 = edge_length ** 2
        r2 = edge2 / (1 - cos(2 * m * pi / n)) / 2
        height2 = edge2 - 2 * r2 * (1 - cos(m * pi / n))
        height_div_2 = sqrt(height2) / 2

        n_gon_top = get_polygon(n, m, height=height_div_2)
        n_gon_bottom = get_polygon(n, m, height=-height_div_2)
        rot_bottom = geomtypes.Rot3(axis=geomtypes.UZ, angle=m * pi / n)

        both = n_gon_top, n_gon_bottom
        # Assuming that all subs have the same length, which should be the case. TODO: assert?
        sub_len = len(both[0][0])
        no_of_subs = len(both[0])

        # It is easier for the sides to sort top and bottom vertices according to angle
        vertices = [
            n_gon_top[sub_i][v_i] for v_i in range(sub_len) for sub_i in range(no_of_subs)
        ] + [
            rot_bottom * n_gon_bottom[sub_i][v_i]
            for v_i in range(sub_len) for sub_i in range(no_of_subs)
        ]
        bases = [
            [
                (v_i * no_of_subs + sub_i) % n + pgon_i * n
                for v_i in range(sub_len)
            ]
            for sub_i in range(no_of_subs)
            for pgon_i in range(2)
        ]
        self.no_of_bases = len(bases)
        triangles = [
            # top attached
            [
                bases[sub_i * 2][v_i],
                # TODO: check + sub_i // no_of_subs for no_of_subs > 2
                bases[(sub_i * 2 + 1) % self.no_of_bases][v_i],
                bases[sub_i * 2][(v_i + 1) % sub_len],
            ]
            for sub_i in range(no_of_subs)
            for v_i in range(sub_len)
        ] + [
            # bottom attached (change order keep counter-clockwise numbering)
            [
                bases[(sub_i * 2 + 1) % self.no_of_bases][v_i],
                bases[(sub_i * 2 + 1) % self.no_of_bases][(v_i + 1) % sub_len],
                # TODO: check + sub_i // no_of_subs for no_of_subs > 2
                bases[sub_i * 2][(v_i + 1) % sub_len],
            ]
            for sub_i in range(no_of_subs)
            for v_i in range(sub_len)
        ]
        # Reverse the bottom base to keep the counter-clockwise order:
        for i in range(1, len(bases), 2):
            bases[i].reverse()
        ring_len = no_of_subs * sub_len
        col_i = [0 for _ in range(self.no_of_bases)] + [
            1 for _ in range(ring_len)
        ] + [
            2 for _ in range(ring_len)
        ]
        super().__init__(
            vertices,
            bases + triangles,
            colors=(cols, col_i),
            name=(f"antiprism_{n}_{m}"),
        )
        if use_outline:
            self.replace_face_by_outline(0)
            self.replace_face_by_outline(1)


class ThreeAntiPrisms(geom_3d.CompoundShape):
    """Compound of three {n/m} anti-prisms all sharing one opposite pairs of triangles."""

    def __init__(
        self,
        n: int,
        m: int = 1,
        edge_length: float = EDGE_LENGTH,
        use_outline: bool = False,
    ) -> geom_3d.CompoundShape:
        """Return an object of three anti-prism with {n/m} base.

        n: n in the {n/m} base
        m: n in the {n/m} base
        edge_length: the required edge length
        use_outline: set to False to use n sides for any {n/m}-gram where m > 1. For orbitit this
            will lead to holes for parts of the polygon that have double coverage. Using the outline
            lead to edges not really being shared between faces, since the {n/m}-gram will have 2n
            edges.
        """
        one = AntiPrism(n, m, edge_length, use_outline=use_outline)
        # The way this is set-up the first triangle goes through X-axis
        triangle = one.fs[one.no_of_bases]
        assert len(triangle) == 3
        orig_to_triangle_gravity = one.vs[triangle[0]] + one.vs[triangle[1]] + one.vs[triangle[2]]

        # The gravity point of the triangle is supposed to be in the XoZ-plane
        with geomtypes.FloatHandler(precision=15) as fh:
            assert fh.eq(orig_to_triangle_gravity[1], 0),\
                f"{orig_to_triangle_gravity} not in XoZ for {{{n}/{m}}}"

        # Rotate around Y-axis so that the gravity point is on Z-axis:
        axis = geomtypes.UY
        angle = orig_to_triangle_gravity.directed_angle(geomtypes.UZ, axis)
        one.transform(geomtypes.Rot3(angle=angle, axis=axis))

        # In some cases the bottom is also shared, e.g. {7/1}, {7/3} and {8/2}
        # In general this happens when the triangles in the anti-prism come in parallel pairs
        # In other cases only to the top triangle is shared, e.g. {4/1} and {7/2}
        self.shared_top_and_bottom = n % 2 == 1 and m % 2 == 1
        self.symmetry = {True: "D3xI", False: "D3C3"}[self.shared_top_and_bottom]

        # When only the top triangle is shared the symmetry is D3C3
        # If both top and bottom are shared, then the symmetry is D3xI
        # Note that D3C3 is a subgroup of D3xI

        # Remove the top triangle and the ones attacted to that one
        bases_offset = 2
        ring_offset = n
        centre_down_i = n // 2
        top_triangle_i = bases_offset
        top_triangle = one.fs[top_triangle_i]
        remove_fs = [top_triangle_i]
        recover_fs = [top_triangle]
        # first and last for second ring are attached
        remove_fs += [bases_offset + ring_offset, bases_offset + ring_offset + n - 1]

        if self.shared_top_and_bottom:
            # For this case both top and bottom triangles are shared by all three anti-prisms
            # Remove all and add single ones later
            bottom_triangle_i = centre_down_i + bases_offset + ring_offset
            bottom_triangle = one.fs[bottom_triangle_i]
            remove_fs.append(bottom_triangle_i)
            recover_fs.append(bottom_triangle)
            # The two in the middle for first ring
            remove_fs += [bases_offset + centre_down_i, bases_offset + centre_down_i + 1]
        one.remove_faces(remove_fs)

        orbit_shape = orbit.Shape(
            {'vs': one.vs, 'fs': one.fs},
            isometry.C3(),
            isometry.E(),
            f"3_antiprism_{n}_{m}_D3xI",
            3,
        )
        shapes = orbit_shape.shapes
        if self.shared_top_and_bottom:
            shapes.append(
                geom_3d.SimpleShape(
                    one.vs,
                    recover_fs,
                    colors=(cols, [3, 3]),
                    name="top_and_bottom"
                )
            )
        else:
            shapes.append(
                geom_3d.SimpleShape(
                    one.vs,
                    [top_triangle],
                    colors=(cols, [3]),
                    name="top"
                )
            )

        super().__init__(orbit_shape.shapes, name=orbit_shape.name)

        # FIXME: case {6/2}, {8/2}, {9/3} aren't working


if __name__ == "__main__":
    folder = "out/tri_composites_of_antriprisms"
    check = [
        (3, 1),
        (4, 1),
        (5, 1), (5, 2),
        (6, 1), (6, 2),
        (7, 1), (7, 2), (7, 3),
        (8, 2),
        (9, 1), (9, 2), (9, 3),
    ]
    for N, M in check:
        star_polygon_basis = M > 1 and not N % M == 0
        tca = ThreeAntiPrisms(N, M)
        with open(f"{folder}/3_antiprims_{N}_{M}_{tca.symmetry}.off", "w") as fd:
            fd.write(tca.to_off())
        if star_polygon_basis:
            # Also create a version using outlines
            tca = ThreeAntiPrisms(N, M, use_outline=True)
            with open(f"{folder}/3_antiprims_{N}_{M}_{tca.symmetry}_outline.off", "w") as fd:
                fd.write(tca.to_off())

    check = [(4, 1), (5, 1), (5, 2), (6, 1), (7, 1), (7, 2), (7, 3), (8, 2), (9, 1), (9, 3)]
    for N, M in check:
        # Use outline here as well
        with open(f"{folder}/antiprims_{N}_{M}.off", "w") as fd:
            fd.write(AntiPrism(N, M).to_off())
