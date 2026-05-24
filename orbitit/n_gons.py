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


class Prism(geom_3d.SimpleShape):
    """An {n/m} prism."""
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
        height_div_2 = edge_length / 2
        n_gon_top = get_polygon(n, m, height=height_div_2)
        n_gon_bottom = get_polygon(n, m, height=-height_div_2)

        # Assuming that all subs have the same length, which should be the case. TODO: assert?
        sub_len = len(n_gon_top[0])
        no_of_subs = len(n_gon_top)

        # just chain all top subs and then all bottom subs
        vertices = [v for sub in n_gon_top for v in sub] + [v for sub in n_gon_bottom for v in sub]

        bases = [
            [i + sub_i * sub_len for i in range(sub_len)]
            for sub_i in range(2 * no_of_subs)
        ]
        # Reverse the bottom base (or top is m > n/2) to keep the counter-clockwise order:
        # Note it is possible to do this right from the beginning, but I think the code is easier to
        # understand this way
        for i in range(no_of_subs, 2 * no_of_subs):
            bases[i].reverse()

        # FIXME: If star polygon and M > N / 2 then all bases need to be reversed.
        # In that case, e.g. of {5/3}, one would like to rotate the base and add crossing squares,
        # but then the sides don't meet
        # TODO: check whether you can do something with that

        sides = [
            [
                side_i + sub_i * sub_len + n,
                (side_i + 1) % sub_len + sub_i * sub_len + n,
                (side_i + 1) % sub_len + sub_i * sub_len,
                side_i + sub_i * sub_len,
            ]
            for sub_i in range(no_of_subs)
            for side_i in range(sub_len)
        ]
        if sub_len % 2 == 1:
            # for odd number of sides, choose one colour (no. 1)
            side_cols = [1 + i for i in range(no_of_subs) for _ in range(sub_len)]
        else:
            # for even number of sides, choose alternating colours
            side_cols = [
                1 + (j % 2) + 2 * i for i in range(no_of_subs) for j in range(sub_len)
            ]
        col_i = [0 for _ in range(2 * no_of_subs)] + side_cols
        super().__init__(
            vertices,
            bases + sides,
            colors=(cols, col_i),
            name=(f"prism_{n}_{m}"),
        )

        # FIXME: I think that if there are subs, since all of them should use outline
        # e.g. {10/4} = 2 x {5/2}
        # same for anti-prism
        if use_outline:
            self.replace_face_by_outline(0)
            self.replace_face_by_outline(1)

class AntiPrism(geom_3d.SimpleShape):
    """An {n/m} anti-prism."""

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
        # TODO: handle n == m, ValueError?
        # Reverse the bottom base (or top is m > n/2) to keep the counter-clockwise order:
        for i in range(1 if m < n / 2 else 0, len(bases), 2):
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


class TwoPrisms(geom_3d.SimpleShape):
    """Compound of three {n/m} anti-prisms all sharing one opposite pairs of triangles."""

    def __init__(
        self,
        n: int,
        m: int = 1,
        edge_length: float = EDGE_LENGTH,
        enhance_cols: bool = True,
    ) -> geom_3d.CompoundShape:
        """Return an object of three anti-prism with {n/m} base.

        n: n in the {n/m} base
        m: n in the {n/m} base
        edge_length: the required edge length
        use_outline: set to False to use n sides for any {n/m}-gram where m > 1. For orbitit this
            will lead to holes for parts of the polygon that have double coverage. Using the outline
            lead to edges not really being shared between faces, since the {n/m}-gram will have 2n
            edges.
        enhance_cols: set to False if you don't care about the colors and in that case only two
            colors will be used. Otherwise effort will be done to divide more colors.
        """
        d = gcd(n, m)

        # If d != 1 then this is a compound. Treat this as a compound
        # TODO: Call TwoPrisms with n_simp and m_simp and generate compound of
        if d != 1:
            # Compound of d {m'/n'} wih m' = m / d and n' = n / d
            # n_simp, m_simp = n // d, m // d

            raise ValueError("TODO: implement this part.")

        # From here on: assume d == 1, i.e. one top and one bottom face per prism
        if n < 2:
            raise ValueError("Only considering BCPs for polygons with more than 2 sides.")
        if n == 4:
            raise ValueError("This leads to cubes, which is a degenerate case.")

        final_sym = isometry.C4(setup={"axis": geomtypes.Vec3([1, 0, 0])})
        stab_sym = isometry.C2(setup={"axis": geomtypes.Vec3([1, 0, 0])})

        name = f"bcp_{m}_{n}"
        base = Prism(n, m, edge_length=edge_length, use_outline= m > 1 and not n % m == 0)
        no_of_cols = 2
        shape = orbit.Shape({'vs': base.vs, 'fs': base.fs}, final_sym, stab_sym, name, no_of_cols)
        double_faces = [0]
        side_offset = 2  # first two faces are top, bottom
        if n % 2 == 0:
            double_faces = [side_offset, side_offset + n // 2]
            no_of_sides = n - 2
        else:
            double_faces = [side_offset]
            no_of_sides = n - 1

        # Give bottom and top separate colors:
        top_i, bottom_i = 0, 1
        extra_col = cols[no_of_cols]
        for shape_no, sub_shape in enumerate(shape.shapes):
            sub_shape.remove_faces(double_faces)
            if enhance_cols:
                sub_shape.update_face_with_col(top_i, extra_col)
                sub_shape.update_face_with_col(bottom_i, extra_col)
                # if n odd, one square side is removed
                # if n even, two square sides are removed
                # In both cases we are left with an even number of sides
                for i in range(shape_no, no_of_sides, 2):
                    sub_shape.update_face_with_col(side_offset + i, cols[no_of_cols + 1 + shape_no])

        single = shape.simple_shape
        super().__init__(single.vs, single.fs, colors=single.shape_colors, name=name)


class ThreeAntiPrisms(geom_3d.SimpleShape):
    """Compound of three {n/m} anti-prisms all sharing one opposite pairs of triangles."""

    def __init__(
        self,
        n: int,
        m: int = 1,
        edge_length: float = EDGE_LENGTH,
        use_outline: bool = False,
        gen_compound: bool = False,
    ) -> geom_3d.CompoundShape:
        """Return an object of three anti-prism with {n/m} base.

        n: n in the {n/m} base
        m: n in the {n/m} base
        edge_length: the required edge length
        use_outline: set to False to use n sides for any {n/m}-gram where m > 1. For orbitit this
            will lead to holes for parts of the polygon that have double coverage. Using the outline
            lead to edges not really being shared between faces, since the {n/m}-gram will have 2n
            edges.
        gen_compound: set to True and a 3-compound of antiprisms is generated instead of a TCA.
        """
        if n < 4:
            raise ValueError("Only considering TCAs for polygons with more than 3 sides.")
        d = gcd(n, m)

        # Compound of d {m'/n'} wih m' = m / d and n' = n / d
        n_simp, m_simp = n // d, m // d

        # In some cases the bottom is also shared, e.g. {7/1}, {7/3} and {8/2}
        # In general this happens when the triangles in the anti-prism come in parallel pairs
        # In other cases only to the top triangle is shared, e.g. {4/1} and {7/2}
        self.shared_top_and_bottom = (n % 2) == (m % 2)

        sym_group = f"D{3}" + {True: "xI", False: f"C{3}"}[self.shared_top_and_bottom]
        head = "" if d == 1 else f"{d}x_"
        self.symmetry = sym_group
        name = f"3_antiprism_{head}{n_simp}_{m_simp}_{sym_group}"
        one = AntiPrism(n, m, edge_length, use_outline=use_outline)
        if d > 1:
            if n_simp < 4:
                raise ValueError(
                    "Only considering compounds of TCAs for polygons with more than 3 sides. "
                    f"The parameters lead to {d} x {{{n_simp}/{m_simp}}}, where {n_simp} <= 3."
                )
        # The way this is set-up the first triangle goes through X-axis
        triangle = one.fs[one.no_of_bases]
        assert len(triangle) == 3
        orig_to_triangle_gravity = one.vs[triangle[0]] + one.vs[triangle[1]] + one.vs[triangle[2]]

        # The gravity point of the triangle is supposed to be in the XoZ-plane
        with geomtypes.FloatHandler(precision=15) as fh:
            assert fh.eq(orig_to_triangle_gravity[1], 0),\
                f"{orig_to_triangle_gravity} not in XoZ for {{{n_simp}/{m_simp}}}"

        # Rotate around Y-axis so that the gravity point is on Z-axis:
        axis = geomtypes.UY
        angle = orig_to_triangle_gravity.directed_angle(geomtypes.UZ, axis)
        one.transform(geomtypes.Rot3(angle=angle, axis=axis))

        # When only the top triangle is shared the symmetry is D3C3
        # If both top and bottom are shared, then the symmetry is D3xI
        # Note that D3C3 is a subgroup of D3xI

        orbit_shape = orbit.Shape(
            {'vs': one.vs, 'fs': one.fs},
            isometry.C3(),
            isometry.E(),
            name,
            3,
        )

        simple_shape = orbit_shape.simple_shape
        if not gen_compound:
            vs, fs, colors = self._handle_multi(simple_shape)
            name = f"TCA_{n}_{m}_{sym_group}"
            super().__init__(vs, fs, colors=colors, name=name)
        else:
            super().__init__(
                simple_shape.vs,
                simple_shape.fs,
                colors=simple_shape.shape_colors,
                name=orbit_shape.name,
            )

    def _handle_multi(self, simple_shape):
        """Handle multiple faces: remove all doubles

        For triple faces: remove two, keep one and change colour.

        Return: vertices, faces, colours
        """
        count_faces = {1: {}, 2: {}, 3: {}}
        clean_shape = simple_shape.clean_shape(10)
        for face_i, face in enumerate(clean_shape.fs):
            min_vi = min(face)
            i = face.index(min_vi)
            face_tuple = tuple(face[i:] + face[:i])
            for occurence in range(1, 4):
                if face_tuple in count_faces[occurence]:
                    count_faces[occurence + 1][face_tuple] = count_faces[occurence][face_tuple]
                    count_faces[occurence + 1][face_tuple].append(face_i)
                    del count_faces[occurence][face_tuple]
                    break
            else:
                count_faces[1][face_tuple] = [face_i]
        # Use all single face occurences
        new_fs_1 = list(count_faces[1].keys())
        cols_1 = [
            clean_shape.shape_colors[1][i] for faces_i in count_faces[1].values() for i in faces_i
        ]
        # Skip double occurences i.e. clean_shape.shape_colors[2]
        # pass
        # Use new colour for triple occurences, but only keep one face
        # assuming that cols[0], cols[1], etc is used in shape_colors
        new_col_index = len(clean_shape.shape_colors[0])
        new_fs_3 = list(count_faces[3].keys())
        cols_3 = [new_col_index for _ in new_fs_3]
        #
        new_fs = new_fs_1 + new_fs_3
        new_cols = (
            clean_shape.shape_colors[0] + tuple([cols[new_col_index]]),
            tuple(cols_1 + cols_3),
        )
        return clean_shape.vs, new_fs, new_cols


if __name__ == "__main__":
    folder = "out/tri_composites_of_antriprisms"
    base_name = "tca"
    check = [
        #(3, 1),
        #(4, 1),
        #(5, 1), (5, 2), (5, 3),
        #(6, 1),
        #(7, 1),
        #(7, 1), (7, 2), (7, 3), (7, 4),
        (7, 3),
        #(8, 1), (8, 2), (8, 3), (8, 5),
        #(9, 1), (9, 2), (9, 4), (9, 5),
        #(10, 1), (10, 2), (10, 3), (10, 4), (10, 6),
        #(12, 3),
    ]
    for N, M in check:
        star_polygon_basis = M > 1 and N % M != 0
        tca = ThreeAntiPrisms(N, M)
        with open(f"{folder}/{base_name}_{N}_{M}_{tca.symmetry}.off", "w") as fd:
            fd.write(tca.to_off())
        if star_polygon_basis:
            # Also create a version using outlines
            tca = ThreeAntiPrisms(N, M, use_outline=True)
            with open(f"{folder}/{base_name}_{N}_{M}_{tca.symmetry}_outline.off", "w") as fd:
                fd.write(tca.to_off())

    check = [(4, 1), (5, 1), (5, 2), (9, 5), (6, 1), (7, 1), (7, 2), (7, 3), (8, 2), (9, 1), (9, 3)]
    check = [
        #(4, 1),
        #(5, 1), (5, 2),
        #(6, 1),
        #(7, 1), (7, 2), (7, 3),
        #(8, 2),
        #(9, 1), (9, 3), (9, 5),
    ]
    for N, M in check:
        # Use outline here as well
        with open(f"{folder}/antiprims_{N}_{M}.off", "w") as fd:
            fd.write(AntiPrism(N, M).to_off())

    folder = "out/bi_composites_of_prisms"
    #base_name = "prism"
    base_name = "bcp"
    check = [
        #(3, 1),
        #(5, 1), (5, 2), (5, 3),
        (6, 1), #(6, 2),
        (7, 1), (7, 2), (7, 3), #(7, 4),
        #(8, 1), (8, 2), (8, 3),
        #(9, 1), (9, 2), (9, 3), (9, 5),
        #(12, 3),
    ]
    for N, M in check:
        star_polygon_basis = M > 1 and not N % M == 0
        #prism = Prism(N, M, use_outline=star_polygon_basis)
        prism = TwoPrisms(N, M)
        with open(f"{folder}/{base_name}_{N}_{M}.off", "w") as fd:
            fd.write(prism.to_off())
