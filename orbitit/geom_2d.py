#!/usr/bin/env python
"""Some geometry definitions that are strictly 2D."""
#
# Copyright (C) 2010 Marcel Tunnissen
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

    def intersect_get_factor(self, l):
        """Gets the factor for the vertex for which the l intersects this line

        I.e. the point of intersection is specified by self.p + result * self.v
        l: the object to intersect with. Currently only a 2D line is supported.

        return: the factor as a geomtypes.RoundedFloat number or None if the object don't share one
        point (e.g.lines are parallel).
        """
        assert isinstance(l, Line), f"Only 2D lines are supported when intersecting, got {l}"
        nom = geomtypes.RoundedFloat(l.v[0] * self.v[1] - l.v[1] * self.v[0])
        if not nom == 0:
            denom = l.v[0] * (l.p[1] - self.p[1]) + l.v[1] * (self.p[0] - l.p[0])
            return geomtypes.RoundedFloat(denom / nom)
        return None

    def intersect(self, l):
        """returns the point of intersection with line l or None if no one solution.

        See intersect_get_factor
        """
        return self.get_point(self.intersect_get_factor(l))

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
        self._es = tuple([(self._vs[i], self.vs[(i + 1) % n]) for i in range(n)])

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

        Each edge is a 2-tuple consisting of indices in self.vs
        """
        return self._es

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
                idx = self._vs[slice(start, n, step)] + self._vs[slice(start_0, stop, step)]
            return [self.coords[i] for i in idx]
        return self.coords[self._vs[key % n]]
