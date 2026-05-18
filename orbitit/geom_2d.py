#!/usr/bin/env python
"""Some geometry definitions that are strictly 2D."""
#
# Copyright (C) 2010-2024 Marcel Tunnissen
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
import math

from orbitit import geomtypes


class Line(geomtypes.Line):
    """Model a line in 2D"""

    def __init__(self, p0, p1=None, v=None, is_segment=False):
        """
        Define a line in a 2D plane.

        Either specify two distinctive points p0 and p1 on the line or specify
        a base point p0 and directional vector v. Points p0 and p1 should have
        accessable [0] and [1] indices.
        """
        geomtypes.Line.__init__(self, p0, p1, v, d=2, is_segment=is_segment)

    def intersect_get_factor(self, obj):
        """Gets the factor for the vertex for which the obj intersects this line

        I.e. the point of intersection is specified by self.p + result * self.v
        obj: the object to intersect with. Currently only a 2D line is supported.

        return: the factor as a geomtypes.RoundedFloat number or None if the object don't share one
        point (e.g.lines are parallel).
        """
        assert isinstance(
            obj, Line
        ), f"Only 2D lines are supported when intersecting, got {obj}"
        nom = geomtypes.RoundedFloat(obj.v[0] * self.v[1] - obj.v[1] * self.v[0])
        if not nom == 0:
            denom = obj.v[0] * (obj.p[1] - self.p[1]) + obj.v[1] * (self.p[0] - obj.p[0])
            return geomtypes.RoundedFloat(denom / nom)
        return None

    def intersect(self, obj):
        """returns the point of intersection with line obj or None if not exactly one solution.

        See intersect_get_factor
        """
        return self.get_point(self.intersect_get_factor(obj))

    def intersect_polygon_get_factors(self, polygon):
        """returns a list of factors where the line inters the polygon 'polygon'.

        polygon: an object of Polygon. The polygon is supposed to be closed.

        return a list of two-tuples which are factors of the line. Each tuple consists of a factor
            where the line enters the polygon and where it exits.
        """
        # TODO: clean up this method: too many branches
        # This list will consist of two-tuples holding:
        # - factors in the line equation
        # - whether or not this factor is optional. Factors become optional when whole edges are on
        #   the line.
        factors = []
        # A pending vertex is a vertex on the line, but depending on the side of prev and next
        # it either needs to be added or not
        pending = None
        # make sure side_of_prev is set
        for idx in range(len(polygon) - 1, -1, -1):
            side_of_prev = self.at_side_of(polygon[idx])
            if side_of_prev:
                break
        else:
            # all vertices are on the line
            return []
        for edge in polygon.es:
            v_current = polygon[edge[0]]
            v_next = polygon[edge[1]]
            side_of_current = self.at_side_of(v_current)
            edge_line = Line(v_current, v_next)
            factor = edge_line.intersect_get_factor(self)
            if factor is not None:
                if 0 < factor < 1:
                    if pending is not None:
                        # There is a vertex on the line that is pending: add only if line crossing
                        if side_of_current != side_of_prev:
                            #            v_current
                            #          /\
                            #  pending/  \ v from factor
                            # --.====*----*---------
                            #  /           \
                            # ._____________\ v_next
                            # v
                            # from side_of_prev
                            factors.append(pending)
                        # else:
                        #     . v from side_of_prev
                        #     |\             v_current
                        #     | \          /\
                        #     |  \ pending/  \ v from factor
                        #     *----======.----*---------
                        #     |                \
                        #     |_________________\ v_next
                        pending = None
                    factors.append(self.intersect_get_factor(edge_line))
                    # Only really needed for two of three situations, but this way no else is needed
                    side_of_prev = side_of_current
                # TODO: use isclose
                elif factor == 0:
                    #      v from side_of_prev
                    #      |     v_next
                    #      /\   /\
                    #     /  \ /  \
                    #   -*----.----*----------
                    #   / v_current \
                    #  /_____________\
                    #
                    # or
                    #
                    #        v from side_of_prev
                    #        /'.
                    #       /   '.
                    #      /      '.
                    #     /         '. v_current
                    #   -*------------*----------
                    #   /              \
                    #  /________________\ v_next
                    #
                    assert pending is None
                    pending = self.intersect_get_factor(edge_line)
                elif factor == 1:
                    # TODO: use isclose
                    if pending is not None:
                        #            v_current
                        #          /\
                        #  pending/  \ v_next
                        # --.====*----*---------
                        #  /           '-_
                        # ._______________'-.
                        # v
                        # from side_of_prev
                        if side_of_current != side_of_prev:
                            factors.append(pending)
                        pending = None
                    # else
                    #        v_current
                    #        /'.
                    #       /   '.
                    #      /      '.
                    #     /         '. v_next
                    #   -*------------*----------
                    #   /              \
                    #  /________________\
                    # v from side_of_prev
                    side_of_prev = side_of_current
                else:
                    # the edge doesn't meet the line between v_current and v_next
                    #     v from side_of_prev
                    #     /\
                    #    /  \           pending
                    # --*----.==========.---------
                    #  /                 \
                    # .                   \ v_current
                    #  '''---___  ___---'''
                    #           '' v_next
                    if pending is not None:
                        if side_of_current != side_of_prev:
                            factors.append(pending)
                        pending = None
            else:
                # i.e. factor is None
                if side_of_current != 0:
                    if pending is not None:
                        if side_of_current != side_of_prev:
                            #     v from side_of_prev
                            #     /\
                            #    /  \           pending
                            # --*----.==========.---------
                            #  /                 \
                            # .___________________\ v_current
                            # v_next
                            factors.append(pending)
                        # else:
                        #     v from side_of_prev ____________v_next
                        #     /\                 /v_current   \
                        #    /  \       pending /              \
                        # --*----.=============.----------------*
                        #  /                                     \
                        # ._______________________________________\
                        # v_next
                        pending = None
                    # else:
                    #      v from side_of_prev
                    #      /\
                    #     /  \
                    #  --*----*---------
                    #   /      \
                    #  .________\ v_current
                    #  v_next
                    #
                    # side_of_current is set above
                # else:
                # the whole edge is on the line,
                #
                #     v from side_of_prev
                #     /\
                #    /  \v_current  v_next
                # --*----.==========.---------
                #  /                 \
                # .___________________\
                #
                # jump to next:
                #  - don't update side_of_current
                #  - the next edge will handle the fact that v_next is also on the line
        if pending is not None:
            side_of_first_v = self.at_side_of(polygon[0])
            # if the 1st vertex of the 1st edge is also on the line, then this is handled already
            if side_of_first_v not in (0, side_of_prev):
                factors.append(pending)
        assert len(factors) % 2 == 0, (
            "There should be an even amount of factors (decrease precision?)"
            f"got the following factors\n\t{factors}\nwith margin {geomtypes.FloatHandler.margin}"
        )
        factors.sort()
        return [(factors[i], factors[i + 1]) for i in range(0, len(factors), 2)]

    def intersect_polygon(self, p):
        """returns a list of segments where the line inters the polygon p.

        See intersect_get_factor
        """
        return [
            (self.get_point(f0), self.get_point(f1))
            for f0, f1 in self.intersect_polygon_get_factors(p)
        ]

    def at_side_of(self, v):
        """Return on which side of the line the vertex is (with respect to the direction v)

        v: a point which should be an instance of geomtypes.Vec with the same dimension of the line.

        return one of the following:
            -1 if the vertex is left of the line
            0 if the vertex is on the line
            1 if the vertex is right of the line
        """
        if self.is_on_line(v):
            return 0
        p0_to_v = v - self.p
        p0_angle = math.atan2(p0_to_v[1], p0_to_v[0])
        line_angle = math.atan2(self.v[1], self.v[0])
        delta = p0_angle - line_angle
        if delta > math.pi:
            delta -= 2 * math.pi
        if delta < -math.pi:
            delta += 2 * math.pi
        if delta < 0:
            return 1
        return -1

    @property
    def angle(self):
        """Return angle with X-axis in radians."""
        return math.atan2(self.v[1], self.v[0])

    def angle_with(self, line):
        """Return from this line to another line in radians."""
        return line.angle - self.angle


class Polygon:
    """Represent a polygon (convex or concave) in 2D.

    The polygon consists of one set of connected edges, i.e. the polygon cannot have a hole
    consisting of unconnected edges.

    The direction of the connected edges are irrelevant.
    """

    def __init__(self, coords, vs):
        """Initialize the polygon

        coords: a list two dimension vertices. There may be any doublets in the list. There might be
            coordinates in the list that aren't used.
        vs: a list of indices expressing which vertices to connect. The last and the first are
            connected implicitely.
        """
        self._coords = tuple(coords)
        self._vs = tuple(vs)
        n = len(self._vs)
        self._es = tuple((i, (i + 1) % n) for i in range(n))

    @property
    def coords(self):
        """Get the tuple of coordinates."""
        return self._coords

    @property
    def vs(self):
        """Get the vertices."""
        return self._vs

    @property
    def es(self):
        """Get the tuple of all edges.

        Each edge is a 2-tuple consisting of indices in self.vs. Note these aren't indices in
            self.coords, i.e. use these in self[..]
        """
        return self._es

    def __len__(self):
        """Return the amount of vertices / edges in the polygon."""
        return len(self._vs)

    def __getitem__(self, key):
        """Return the coordinate of specified slice modulo the amount of vertices.

        The slice will always result in maximum of one whole polygon.
        """
        n = len(self._vs)
        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            if stop <= start:
                # TODO: in this case you should itemize in the opposite direction
                return []
            start = start % n
            if stop % n == 0:
                stop = n
            else:
                stop = stop % n
            if step is None:
                step = 1
            if start < stop:
                idx = self._vs[slice(start, stop, step)]
            else:
                # wrap around
                if start == stop:
                    start -= n
                start_0 = step - (start - n) % step - 1
                idx = (
                    self._vs[slice(start, n, step)]
                    + self._vs[slice(start_0, stop, step)]
                )
            return [self.coords[i] for i in idx]
        return self.coords[self._vs[key % n]]
