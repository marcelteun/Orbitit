#!/usr/bin/env python
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
# Old sins:
# pylint: disable=too-many-lines,too-many-return-statements,
# pylint: disable=too-many-locals,too-many-statements,too-many-ancestors
# pylint: disable=too-many-instance-attributes,too-many-arguments
# pylint: disable=too-many-branches,too-many-nested-blocks
# pylint: disable=too-few-public-methods,too-many-public-methods


from abc import ABC
import copy
import logging
import math
from functools import reduce
import wx

from OpenGL import GL

from orbitit import base, geomtypes, glue, indent, isometry, PS, rgb, Scenes3D

# TODO:
# - Test the gl stuf of SimpleShape: create an Interactive3DCanvas
#   the Symmetry stuff should not contain any shape stuff
# - Add a flatten option to the Symmetric Face: resulting will be a SimpleShape
#   that can be exported.
# - Add class function: intersect faces: which will return a new shape for
#   which the faces do not intersect anymore. Then there should be a class
#   function for converting the faces to PS string as is.
# - remove depedency towards cgkit: move to Scientific Python: make your own
#   wrapper to abstract from this dependency?
# - Add possible scene objects, containing shapes.
# - add transforms
# - add print pieces (cp from p3D)
# - function to_postscript finds intersection: this should be part of a separate
#   functons mapping the SimpleShape on a shape consisting of none intersecting
#   pieces. This could be a child of SimpleShape.
# - add function to filter out vertices that ly within a certain area: these
#   should be projected on the avg of all of them: use a counter for this.
# - clean up a bit: some functions return objects, other return the strings.

# Done
# - edges after reading off file

VEC = lambda x, y, z: geomtypes.Vec3([x, y, z])

E = geomtypes.E  # Identity
I = geomtypes.I  # Central inversion

# constant that have deal with angles
Rad2Deg = 180.0 / math.pi
Deg2Rad = math.pi / 180
R1_2 = math.pi  # 1/2 of a circle

R1_3 = 2 * math.pi / 3  # 1/3 of a circle
R2_3 = 2 * R1_3  # 2/3 of a circle

R1_4 = math.pi / 2  # 1/4 of a circle
R3_4 = 3 * R1_4  # 3/4 of a circle

R1_5 = 2 * math.pi / 5  # 1/5 of a circle
R2_5 = 2 * R1_5  # 2/5 of a circle
R3_5 = 3 * R1_5  # 3/5 of a circle
R4_5 = 4 * R1_5  # 4/5 of a circle

V2 = math.sqrt(2)
V3 = math.sqrt(3)
V5 = math.sqrt(5)

TAU = (V5 + 1) / 2

# rotation needed from standard isometries.A4 where the z-axis is shared with a 2-fold axis to a
# position where the z-axis is shared with a 3-fold axis.
A4_Z_O2_TO_O3 = geomtypes.Rot3(angle=math.atan(V2), axis=geomtypes.Vec3([1, 1, 0]))
A4_Z_O2_TO_O3 = geomtypes.Rot3(angle=math.pi / 4, axis=geomtypes.Vec3([0, 0, 1])) * A4_Z_O2_TO_O3

S4_Z_O4_TO_O3 = A4_Z_O2_TO_O3
S4_Z_O4_TO_O2 = geomtypes.Rot3(angle=math.pi / 4, axis=geomtypes.Vec3([0, 1, 0]))

# rotation needed from standard isometries.A5 where the z-axis is shared with a 2-fold axis to a
# position where the z-axis is shared with a 5-fold axis
A5_Z_O2_TO_O5 = geomtypes.Rot3(angle=math.atan(TAU), axis=geomtypes.Vec3([1, 0, 0]))

# rotation needed from standard isometries.A5 where the z-axis is shared with a 2-fold axis to a
# position where the z-axis is shared with a 3-fold axis
A5_Z_O2_TO_O3 = geomtypes.Rot3(angle=math.atan(2 - TAU), axis=geomtypes.Vec3([1, 0, 0]))


def is_int(int_str):
    """Return whether the string represents an integer."""
    try:
        _ = int(int_str)
        return True
    except ValueError:
        return False


def read_off_file(fd, regen_edges=True, name=""):
    """Reads an the std 'off' format of a 3D object and returns an object of the
    SimpleShape class.

    fd: the file descriptor of a file that is opened with read permissions.
    regen_edges: if set to True then the shape will recreate the edges for all faces, i.e. all faces
        will be surrounded by edges. Edges will be filtered so that shared edges between faces, i.e.
        edges that have the same vertex index, only appear once. The creation of edges is not
        optimised and can take a long time.
    return: an object of the SimpleShape class.
    """
    states = {"checkOff": 0, "readSizes": 1, "readVs": 2, "readFs": 3, "readOk": 4}
    no_of_vs = 0
    no_of_fs = 0
    no_of_es = 0
    es = []
    i = 0
    # A dictionary where the key and value pairs are exchanged, for debugging
    # purposes:
    statesRev = {}
    for (key, value) in states.items():
        statesRev[value] = key
    state = states["checkOff"]
    vRadius = 0
    eRadius = 0
    for line in fd:
        words = line.split()
        if len(words) > 0 and words[0][0] != "#":
            if state == states["checkOff"]:
                if words[0] == "OFF":
                    state = states["readSizes"]
                else:
                    break
                logging.debug("OFF file format recognised")
            elif state == states["readSizes"]:
                # the function assumes: no comments in beween the 3 nrs
                assert words[0].isdigit()
                assert words[1].isdigit()
                assert words[2].isdigit()
                no_of_vs = int(words[0])
                no_of_fs = int(words[1])
                no_of_es = int(words[2])
                # Dont check Euler: in a compound for each part F + V - E = 2
                # So the difference 2 becomes 2n for a compound of n.
                # assert no_of_es + 2 == no_of_fs + no_of_vs
                state = states["readVs"]
                vs = []
                logging.debug(
                    "will read %d vertices, %d faces and %d edges",
                    no_of_vs,
                    no_of_fs,
                    no_of_es,
                )
            elif state == states["readVs"]:
                # the function assumes: no comments in beween (x, y, z) of vs
                vs.append(geomtypes.Vec3(words[0:3]))
                logging.debug("V[%d] = %s", i, vs[-1])
                i = i + 1
                if i == no_of_vs:
                    state = states["readFs"]
                    fs = []
                    cols = []
                    face_cols = [i for i in range(no_of_fs)]
                    i = 0
                    if no_of_fs == 0:
                        state = states["readOk"]
                        logging.info("Note: the OFF file only contains vertices")
                        vRadius = 0.05
            elif state == states["readFs"]:
                # the function assumes: no comments in beween "q i0 .. iq-1 r g b"
                assert words[0].isdigit(), "error interpreting line as face {}".format(
                    words
                )
                len_f = int(words[0])
                if len_f > 0:
                    assert len(words) >= len_f + 4 or len(words) == len_f + 1
                    face = [int(words[j]) for j in range(1, len_f + 1)]
                    if len_f >= 3:
                        fs.append(face)
                        if len(words) == len_f + 1:
                            cols.append([0.8, 0.8, 0.8])
                        else:
                            if is_int(words[len_f + 1]):
                                cols.append(
                                    [
                                        float(words[j]) / 255
                                        for j in range(len_f + 1, len_f + 4)
                                    ]
                                )
                            else:
                                cols.append(
                                    [
                                        float(words[j])
                                        for j in range(len_f + 1, len_f + 4)
                                    ]
                                )
                        logging.debug("face[%d] = %s", i, fs[-1])
                        logging.debug("col[%d] = %s", i, cols[-1])
                    else:
                        if len_f == 2:
                            # this is an edge really...
                            es.extend(face)
                            eRadius = 0.15
                            logging.debug("face[%d] = %s is an edge", i, face)
                            # what about different edge colours?
                        else:
                            # since vertices are defined explicitely, show them
                            vRadius = 0.05
                            logging.info("ignoring face %d with only %d vertices", i, len_f)
                    i = i + 1
                    if i == no_of_fs:
                        state = states["readOk"]
                        break
            else:
                break
    assert (
        state == states["readOk"]
    ), """
        EOF occurred while not done reading:
            Would read %d vs and %d fs;
            current state %s with %d items read""" % (
        no_of_vs,
        no_of_fs,
        statesRev[state],
        i,
    )
    shape = SimpleShape(vs, fs, es, colors=(cols, face_cols))
    # Note that Orbitit's panel.setShape will ignore these anyway...
    if vRadius != 0:
        shape.vertex_props = {'radius': vRadius}
    if eRadius != 0:
        shape.edge_props = {'radius': eRadius}
    if name != "":
        shape.name = name
    # If the file defines edges (faces of length 2) then don't recreate any
    # edges, even if requested
    if regen_edges and len(es) == 0:
        shape.regen_edges()
    return shape


def saveFile(fd, shape):
    """
    Save a shape in a file descriptor

    The caller still need to close the filde descriptor afterwards
    """
    fd.write("import orbitit\n")
    fd.write("shape = %s" % repr(shape))


class Fields:
    """
    This class is an empty class to be able to set some fields, like structures
    in C.
    """

    pass


class PrecisionError(ValueError):
    "Possible error caused bby floats not being equals exactly"


class Line:
    def __init__(self, p0, p1=None, v=None, d=3, isSegment=False):
        """
        Define a line in a d dimensional space.

        Either specify two distinctive points p0 and p1 on the d dimensional
        line or specify a base point p0 and directional vector v. Points p0 and
        p1 should have accessable [0] .. [d-1] indices.
        """
        assert (
            p1 is None or v is None
        ), "Specify either 2 points p0 and p1 or a base point p0 and a direction v!"
        self.dimension = len(p0)
        self.isSegment = isSegment
        if p1 is not None:
            self.setPoints(p0, p1)
        elif v is not None:
            self.setBaseDir(p0, v)

    def setPoints(self, p0, p1):
        d = [p1[i] - p0[i] for i in range(self.dimension)]
        self.setBaseDir(p0, d)

    def setBaseDir(self, p, v):
        self.p = p
        self.v = v

    def getPoint(self, t):
        """Returns the point on the line that equals to self.b + t*self.v (or [] when t is None)

        return: the point is an instance of geomtypes.Vec
        """
        if t is not None:
            return geomtypes.Vec([self.p[i] + t * (self.v[i]) for i in range(self.dimension)])
        return geomtypes.Vec([])

    def getFactorAt(self, c, i):
        """
        For an n-dimensional line l = p + t.v it get the factor t for which p[i] + t.v[i] = c

        c: the constant
        i: index of element that should equal to c

        return: a RoundedFloat number or None if:
           1. the line lies in the (n-1) (hyper)plane x_i == c
           2. or the line never intersects the (n-1) (hyper)plane x_i == c.
        """
        if not geomtypes.FloatHandler.eq(self.v[i], 0.0):
            return geomtypes.RoundedFloat((c - self.p[i]) / self.v[i])
        return None

    def vOnLine(self, v):
        """
        Return True is V is on the line, False otherwise

        v: a point which should be an instance of geomtypes.Vec with the same dimension of the line.
        """
        t = self.getFactorAt(v[0], 0)
        if t is None:
            t = self.getFactorAt(v[1], 1)
        assert t is not None
        return self.getPoint(t) == v

    def getFactor(self, p, check=True):
        """Assuming the point p lies on the line, the factor is returned.

        If the line is a segment. i.e. if the line isn't infinite a ValueError is raised if it
        isn't on the segment.

        p: a point which should be an instance of geomtypes.Vec
        check: if set, then the method will check whether the point is on the line using the current
        precision of geomtypes.FloatHandler. If not a ValueError is raised.

        """
        for i in range(self.dimension):
            t = self.getFactorAt(p[i], i)
            if not t is None:
                break
        assert t is not None
        if check:
            c = self.getPoint(t)
            if not c == p[:self.dimension]:
                logging.warning(
                    "The point is not on the line; yDiff = %f", c[i] - p[i]
                )
                raise ValueError("The point is not on the line according to the current precision")
        if self.isSegment:
            if not (0 <= t <= 1):
                logging.warning("The point is not on the line segment; t = %f not in [0, 1]", t)
                raise ValueError("The point is not on the line segment (with current precisio)")
        return t


    def __repr__(self):
        """Get a string representation of the line."""
        return f"{self.p} + t.{self.v}"


class Line2D(Line):
    def __init__(self, p0, p1=None, v=None, isSegment=False):
        """
        Define a line in a 2D plane.

        Either specify two distinctive points p0 and p1 on the line or specify
        a base point p0 and directional vector v. Points p0 and p1 should have
        accessable [0] and [1] indices.
        """
        Line.__init__(self, p0, p1, v, d=2, isSegment=isSegment)

    def intersectLineGetFactor(self, l):
        """Gets the factor for v for which the line l intersects this line

        i.e. the point of intersection is specified by self.p + restult * self.v

        return: the factor as a geomtypes.RoundedFloat number or None if the lines are parallel.
        """
        nom = geomtypes.RoundedFloat(l.v[0] * self.v[1] - l.v[1] * self.v[0])
        if not nom == 0:
            denom = l.v[0] * (l.p[1] - self.p[1]) + l.v[1] * (self.p[0] - l.p[0])
            return geomtypes.RoundedFloat(denom / nom)
        return None

    def intersectLine(self, l):
        """returns the point of intersection with line l or None if the line is parallel."""
        return self.getPoint(self.intersectLineGetFactor(l))

    # FIXME: this is a weird method to have here.
    def intersect_with_face(
        self,
        FacetVs,
        iFacet,
        z0=0.0,
    ):
        """
        Intersect the 2D line object in plane z = Z0 with a 3D facet

        The 2D line object is lying in plane z = z0.
        The result is cleaned up in such a way that intersections with vertices
        that just touch the a vertex without entering or exiting the facet are
        removed.

        FacetVs: the (possible 3 dimensional) vertices
        iFacet: the indices that form this facet. The indices refer to FacetVs
        z0    : defines the plane in which the 2D line is lying

        return:
        A list with the factors of the line where it intersects the edges.
        """
        # Algorithm:
        # PART 1.
        # For each edge is checked if it intersects plane z = z0 in a point.
        # If so the algorithm calculates the intersection point and checks if it
        # lies on the line.
        # If the edge lies in the plane the intersection of the 2 lines 2D are
        # calculated.
        # Otherwise the edges is parallel to the plane z = z0: no intersection.
        #
        # pOnLineAtEdges contains the factors in a line for the points where
        # the line intersects the sides of iFacet.
        z0 = geomtypes.RoundedFloat(z0)
        pOnLineAtEdges = []
        no_of_vs = len(iFacet)
        logging.debug("facet indices: %s", iFacet)
        vertexIntersections = []
        for vertexNr in range(no_of_vs):
            v0 = FacetVs[iFacet[vertexNr]]
            v1 = FacetVs[iFacet[(vertexNr + 1) % no_of_vs]]
            v0 = geomtypes.Vec(v0)
            v1 = geomtypes.Vec(v1)
            logging.debug(
                "==> intersect line with edge nr %d = %s -> %s",
                vertexNr,
                v0,
                v1,
            )
            logging.debug("(with this current line object: %s + t*%s)", self.p, self.v)

            # PART 1.
            edgePV3D = Line3D(v0, v=v1 - v0)
            t = edgePV3D.getFactorAt(z0, 2)
            s = None
            if t is not None:
                if 0 <= t <= 1:
                    logging.debug(
                        "edge intersects plane z = %f, in a point (t = %f)", z0, t
                    )
                    try:
                        s = self.getFactor(edgePV3D.getPoint(t))
                    except ValueError:
                        s = None
                else:
                    logging.debug(
                        "edge intersects plane z = %f but only if extended (t = %f)", z0, t
                    )
            else:
                # Either the edge lies in the plane z = z0
                # or it is parallel with this plane
                if z0 == v0[2]:
                    logging.debug("edge lies in plane z = %f", z0)
                    edgePV2D = Line2D(v0, v=v1 - v0)
                    t = edgePV2D.intersectLineGetFactor(self)
                    if t is not None:
                        if 0 <= t <= 1:
                            s = self.intersectLineGetFactor(edgePV2D)
                        else:
                            logging.debug("edge intersects line but only if extended (t = %f)", t)
                    else:
                        # fix getFactor so that just getFactor is needed.
                        if self.vOnLine(v0):
                            t = 0
                            s = self.getFactor(v0)
                            logging.debug("edge is on the line")
                        else:
                            logging.debug("edge is parallel to the line")
                else:
                    logging.debug("edge parallel to plane z = %f (no point of intersection)", z0)
            if s is not None:
                logging.debug("FOUND s = %s with v = %s", s, self.getPoint(s))
                # only add vertex intersections once (otherwise you add the
                # intersection for edge_i and edge_i+1
                if t != 1:
                    # each item is an array that holds
                    # 0. the vertex nr
                    # 1. the index of s in pOnLineAtEdges
                    if t == 0:
                        vertexIntersections.append([vertexNr, len(pOnLineAtEdges)])
                        logging.debug("vertex intersection at v0")
                    pOnLineAtEdges.append(s)
                    logging.debug("added s = %s", s)
                else:
                    logging.debug("vertex intersection at v1, ignored")

        logging.debug("line intersects edges (vertices) at s = %s", pOnLineAtEdges)
        logging.debug("vertex intersections: %s", vertexIntersections)
        nrOfIntersectionsWithVertices = len(vertexIntersections)
        allowOddNrOfIntersections = False
        if nrOfIntersectionsWithVertices == 0:
            pass
        elif nrOfIntersectionsWithVertices == 1:
            # remove if nr of intersections is odd:
            if len(pOnLineAtEdges) % 2 == 0:
                # e.g. and intersection through a vertex and an edge:
                pass
            else:
                # e.g. the line touches a vertex
                # remove:
                del pOnLineAtEdges[vertexIntersections[0][1]]
        elif nrOfIntersectionsWithVertices == 2:
            # if these 2 vertices form an edge:
            vertexIndexDelta = vertexIntersections[1][0] - vertexIntersections[0][0]
            if vertexIndexDelta == 1 or vertexIndexDelta == no_of_vs - 1:
                # (part of) the line of intersection is an edge
                # keep it (note that the edge might continue in a line of
                # intersection for a concave facet, which might lead to an odd
                # nr of intersections.
                allowOddNrOfIntersections = True
        else:
            # check if all vertices are lying on one line:
            allOnOneEdge = True
            for vdI in range(nrOfIntersectionsWithVertices - 1):
                vertexIndexDelta = vertexIntersections[1][0] - vertexIntersections[0][0]
                # e.g. a heptagon that is really a pentagon, since it happens
                # twice that 3 vertices ly on one line: v0, v1, v2 and  v0, v5,
                # v6. So either a difference of 1 or at least 5 is allowed.
                if not (
                    vertexIndexDelta == 1
                    or vertexIndexDelta
                    >= no_of_vs - (nrOfIntersectionsWithVertices - 1)
                ):
                    allOnOneEdge = False
            if allOnOneEdge:
                # see remark above for nrOfIntersectionsWithVertices == 2
                allowOddNrOfIntersections = True
            else:
                # more than 2: complex cases.
                logging.debug(
                    "Intersections through more than 2 vertices (not on one edge)\n"
                    "\tvertexIntersections: %s\n"
                    "\tpOnLineAtEdges: %s\n"
                    "\twill draw one long line, instead of segments",
                    vertexIntersections,
                    pOnLineAtEdges
                )
                # assert False, 'ToDo'
                # if an assert is not wanted, choose pass.
                # allowOddNrOfIntersections = True
                pOnLineAtEdges.sort()
                pOnLineAtEdges = [pOnLineAtEdges[0], pOnLineAtEdges[-1]]
                logging.debug("\tusing pOnLineAtEdges %s", pOnLineAtEdges)
        pOnLineAtEdges.sort()

        logging.debug("pOnLineAtEdges %s after clean up", pOnLineAtEdges)
        assert len(pOnLineAtEdges) % 2 == 0 or allowOddNrOfIntersections, (
            "The nr of intersections should be even, "
            "are all edges unique and do they form one closed face?"
        )
        return pOnLineAtEdges


class Line3D(Line):
    str_precision = 2

    def __init__(self, p0, p1=None, v=None, isSegment=False):
        """
        Define a line in 3D space.

        Either specify two distinctive points p0 and p1 on the line or specify
        a base point p0 and directional vector v. Points p0 and p1 should have
        a length of 3 and may be a geom_types.Vec3 type.
        """
        # make sure to have vector types internally
        p0 = geomtypes.Vec3(p0)
        if p1 is None:
            assert v is not None
            v = geomtypes.Vec3(v)
            Line.__init__(self, p0, v=v, d=3, isSegment=isSegment)
        else:
            assert v is None
            p1 = geomtypes.Vec3(p1)
            Line.__init__(self, p0, p1, d=3, isSegment=isSegment)

    # redefine to get vec3 types:
    def setPoints(self, p0, p1):
        self.setBaseDir(p0, p1 - p0)

    def getPoint(self, t):
        if t is not None:
            return self.p + t * self.v
        return []

    def squareDistance2Point(self, P):
        # p81 of E.Lengyel
        q = geomtypes.Vec3(P)
        hyp = q - self.p
        prjQ = hyp * self.v
        return (hyp * hyp) - ((prjQ * prjQ) / (self.v * self.v))

    def Discriminant2Line(self, L):
        # p82 of E.Lengyel
        dot = self.v * L.v
        return (self.v * self.v) * (L.v * L.v) - dot * dot

    def isParallel2Line(self, L):
        # p82 of E.Lengyel
        return self.Discriminant2Line(L) == 0

    def __str__(self):
        precision = self.str_precision
        format_str = (
            "(x, y, z) = (%%0.%df, %%0.%df, %%0.%df) + t * (%%0.%df, %%0.%df, %%0.%df)"
            % (precision, precision, precision, precision, precision, precision)
        )
        return format_str % (
            self.p[0],
            self.p[1],
            self.p[2],
            self.v[0],
            self.v[1],
            self.v[2],
        )


class Triangle:
    def __init__(self, v0, v1, v2):
        self.v = [
            VEC(v0[0], v0[1], v0[2]),
            VEC(v1[0], v1[1], v1[2]),
            VEC(v2[0], v2[1], v2[2]),
        ]
        self.N = None

    def normal(self, normalise=False):
        if self.N is None:
            self.N = (self.v[1] - self.v[0]).cross(self.v[2] - self.v[0])
            if normalise:
                try:
                    self.N = self.N.normalize()
                except ZeroDivisionError:
                    pass
            return self.N
        return self.N


class PlaneFromNormal:
    """Create a plane from a normal and one known point

    The plane class will contain the fields 'N' expressing the normalised norm
    and a 'D' such that for a point P in the plane 'D' = -N.P, i.e. Nx x + Ny y
    + Nz z + D = 0 is the equation of the plane.
    """
    def __init__(self, normal, point):
        self.N = normal
        self.D = geomtypes.RoundedFloat(-self.N * geomtypes.Vec3(point))

    def intersect_with_plane(self, plane):
        """Calculates the intersections of 2 planes.

        If the planes are parallel None is returned (even if the planes define
        the same plane) otherwise a line is returned.
        """
        if plane is None:
            return None
        n0 = self.N
        n1 = plane.N
        if n0 == n1 or n0 == -n1:
            return None
        V = n0.cross(n1)
        # V = V.normalise()
        # for to_postscript self.N == [0, 0, 1]; handle more efficiently.
        if n0 == geomtypes.Vec([0, 0, 1]):
            # simplified situation from below:
            z = -self.D
            M = geomtypes.Mat([geomtypes.Vec(n1[0:2]), geomtypes.Vec(V[0:2])])
            Q = M.solve(geomtypes.Vec([-plane.D - n1[2] * z, -V[2] * z]))
            Q = geomtypes.Vec([Q[0], Q[1], z])
        else:
            # See bottom of page 86 of Maths for 3D Game Programming.
            M = geomtypes.Mat([n0, n1, V])
            Q = M.solve(geomtypes.Vec([-self.D, -plane.D, 0]))
        return Line3D(Q, v=V)

    def __eq__(self, plane):
        """Return True if the planes define the same one."""
        return (
            self.N == plane.N and self.D == plane.D
        ) or (
            self.N == -plane.N and self.D == -plane.D
        )

    def __repr__(self):
        return "{} x + {} y + {} z + {} = 0".format(
            geomtypes.RoundedFloat(self.N[0]),
            geomtypes.RoundedFloat(self.N[1]),
            geomtypes.RoundedFloat(self.N[2]),
            self.D
        )

class Plane(PlaneFromNormal):
    """Create a plane from 3 points in the plane.

    The points should be unique.
    """
    def __init__(self, P0, P1, P2):
        assert not P0 == P1, "\n  P0 = %s,\n  P1 = %s" % (str(P0), str(P1))
        assert not P0 == P2, "\n  P0 = %s,\n  P2 = %s" % (str(P0), str(P2))
        assert not P1 == P2, "\n  P1 = %s,\n  P2 = %s" % (str(P1), str(P2))
        self.N = self._norm(P0, P1, P2)
        self.D = geomtypes.RoundedFloat(-self.N * geomtypes.Vec3(P0))

    @staticmethod
    def _norm(P0, P1, P2):
        """calculate the normalised plane normal"""
        v1 = geomtypes.Vec3(P0) - geomtypes.Vec3(P1)
        v2 = geomtypes.Vec3(P0) - geomtypes.Vec3(P2)
        cross = v1.cross(v2)
        if geomtypes.FloatHandler.eq(cross.norm(), 0):
            raise ValueError("Points are on one line")
        result = v1.cross(v2).normalize()
        return result


TRI_CW = 1  # clockwise triangle vertices to get outer normal
TRI_CCW = 2  # counter-clockwise triangle vertices to get outer normal
TRI_OUT = 3  # the normal pointing away from the origin is the normal
TRI_IN = 4  # the normal pointing towards from the origin is the normal


class SimpleShape(base.Orbitit):
    normal_direction = TRI_OUT

    """
    This class decribes a simple 3D object consisting of faces and edges.

    Attributes:
    shape_colors: same as the colors parameter in __init__, see that method.
    """

    def __init__(
        self, vs, fs, es=None, ns=None, colors=None, name="SimpleShape", orientation=None
    ):
        """
        vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by gl_draw
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each face with
                   index 'i' in fs which colour index from the parameter color
                   is used for this face.  If empty then colors[0][0] shall be
                   used for each face.
        name: A string expressing the name. This name is used e.g. when
            exporting to other formats, like PS.
        orientation: orientation of the base shape. This is an isometry operation.
        """
        if not es:
            es = []
        if not ns:
            ns = []
        self.dimension = 3
        self.face_normals = []
        self.generate_normals = True
        self.name = name
        self.gl_initialised = False
        self.gl = Fields()
        self.gl.sphere = None
        self.gl.cyl = None
        # This is save so heirs can still use repr_dict from this class
        self.json_class = SimpleShape
        self.gl.alwaysSetVertices = (
            False  # set to true if a scene contains more than 1 shape
        )
        if not colors or not colors[0]:
            colors = ([rgb.gray95[:]], [])
        self.zoom_factor = 1.0
        self.vertex_props = {'vs': vs, 'ns': ns, 'radius': -1.0, 'color': [1.0, 1.0, 0.8]}
        self.edge_props = {'es': es, 'radius': -1.0, 'color': [0.1, 0.1, 0.1], 'draw_edges': True}
        self.face_props = {'fs': fs, 'colors': colors, 'draw_faces': True}
        self.defaultColor = rgb.yellow
        if orientation:
            self.orientation = orientation
            if not orientation.is_rot():
                self.normal_direction = TRI_IN
        else:
            self.orientation = geomtypes.E

    def __repr__(self):
        # s = indent.Str('%s(\n' % base.find_module_class_name(self.__class__, __name__))
        s = indent.Str("SimpleShape(\n")
        s = s.add_incr_line("vs=[")
        s.incr()
        try:
            s = s.glue_line(
                ",\n".join(indent.Str(repr(v)).reindent(s.indent) for v in self.vs)
            )
        except AttributeError:
            logging.error("Are you sure the vertices are all of type geomtypes.Vec3?")
            raise
        s = s.add_decr_line("],")
        s = s.add_line("fs=[")
        s.incr()
        s = s.glue_line(
            ",\n".join(indent.Str(repr(f)).reindent(s.indent) for f in self.fs)
        )
        s = s.add_decr_line("],")
        s = s.add_line("es=%s," % repr(self.es))
        s = s.add_line("colors=%s," % repr(self._shape_colors))
        s = s.add_line('name="%s"' % self.name)
        s = s.add_decr_line(")")
        if __name__ != "__main__":
            s = s.insert("%s." % __name__)
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object.

        Only essential parts are saved. E.g. orientation isn't essential here.
        """
        return {
            "class": base.class_to_json[self.json_class],
            "data": {
                "name": self.name,
                "vs": self.vs,
                "fs": self.fs,
                "cols": self._shape_colors[0],
                "face_cols": self._shape_colors[1],
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        return cls(
            [geomtypes.Vec3(v) for v in data["vs"]],
            data["fs"],
            colors=(data["cols"], data["face_cols"]),
            name=data["name"],
        )

    def saveFile(self, fd):
        """
        Save a shape in a file descriptor

        The caller still need to close the filde descriptor afterwards
        """
        saveFile(fd, self)

    @property
    def simple_shape(self):
        """To be compatible: derivatives of this class will have this property

        Some classes that inherit from this class need to implement self.
        Implement here to be compatible.
        """
        return self

    def filter_faces(self, keep_one=True):
        """Remove faces using the same vertices (independent of their colour)

        keep_one: of the faces with duplicates keep at least one.
        """
        v_props = self.vertex_props
        f_props = self.face_props
        fs = f_props["fs"]
        org_cols = f_props["colors"]
        d = dict()
        for i, face in enumerate(fs):
            face_cp = face[:]
            face_cp.sort()
            try:
                d[tuple(face_cp)].append(i)
            except KeyError:
                d[tuple(face_cp)] = [i]

        new_fs = []
        col_idx = []
        if keep_one:
            for f in d:
                new_fs.append(fs[i[0]])
                col_idx.append(org_cols[1][i[0]])
        else:
            for f, i in d.items():
                if len(i) == 1:
                    new_fs.append(fs[i[0]])
                    col_idx.append(org_cols[1][i[0]])
        new_cols = (copy.deepcopy(org_cols[0]), col_idx)
        shape = SimpleShape([], [], [])
        shape.vertex_props = v_props
        f_props["fs"] = new_fs
        f_props["colors"] = new_cols
        shape.face_props = f_props
        return shape

    def clean_shape(self, precision):
        """Return a new shape for which vertices are merged and degenerated faces are deleted.

        The shape will not have any edges.

        precision: number of decimals to consider when deciding whether two floating point numbers
            are equal.
        """
        vProps = self.vertex_props
        fProps = self.face_props
        cpVs = copy.deepcopy(vProps["vs"])
        cpFs = copy.deepcopy(fProps["fs"])
        with geomtypes.FloatHandler(precision):
            glue.mergeVs(cpVs, cpFs, precision)
        # this may result on less faces, which breaks the colours!
        # TODO either update the colors immediately or return an array with
        # deleted face indices.
        glue.cleanUpVsFs(cpVs, cpFs)
        vProps["vs"] = cpVs
        fProps["fs"] = cpFs
        shape = SimpleShape([], [], [])
        shape.vertex_props = vProps
        shape.face_props = fProps
        return shape

    @property
    def vertex_props(self):
        """
        Return the current vertex properties

        Returned is a dictionary with the keywords vs, radius, color and ns.
        vs: an array of vertices.
        radius: If > 0.0 draw vertices as spheres with the specified colour. If
                no spheres are required (for preformance reasons) set the radius
                to a value <= 0.0.
        color: optianl array with 3 rgb values between 0 and 1.
        ns: an array of normals (per vertex) This value might be None if the
            value is not set. If the value is set it is used by gl_draw
        """
        return {
            "vs": self.vs,
            "radius": self.gl.vRadius,
            "color": self.gl.vCol,
            "ns": self.ns,
        }

    @vertex_props.setter
    def vertex_props(self, props):
        """
        Set the vertices and how/whether vertices are drawn in OpenGL.

        Accepted are the optional (keys) parameters:
        - vs,
        - radius,
        - color.
        - ns.
        See getter for the explanation of the keys.
        """
        if props:
            if "vs" in props and props["vs"] is not None:
                self.vs = [geomtypes.Vec3(v) for v in props["vs"]]
                self.VsRange = range(len(self.vs))
                self.gl.updateVs = True
                self.face_normals_up_to_date = False
            if "ns" in props and props["ns"] is not None:
                self.ns = props["ns"]
            if "radius" in props and props["radius"] is not None:
                self.gl.vRadius = props["radius"]
                self.gl.addSphereVs = props["radius"] > 0.0
                if self.gl.addSphereVs:
                    if self.gl.sphere is not None:
                        del self.gl.sphere
                    self.gl.sphere = Scenes3D.VSphere(radius=props["radius"])
            if "color" in props and props["color"] is not None:
                self.gl.vCol = props["color"]

    def gl_alwaysSetVertices(self, do):
        self.gl.alwaysSetVertices = do

    @property
    def edge_props(self):
        """
        Return the current edge properties

        Returned is a dictionary with the keywords es, radius, color, draw_edges
        es: a qD array of edges, where i and j in edge [ .., i, j,.. ] are
            indices in vs.
        radius: If > 0.0 draw vertices as cylinders with the specified colour.
                If no cylinders are required (for preformance reasons) set the
                radius to a value <= 0.0 and the edges will be drawn as lines,
                using glPolygonOffset.
        color: array with 3 rgb values between 0 and 1.
        draw_edges: settings that expresses whether the edges should be drawn at all.
        """
        return {
            "es": self.es,
            "radius": self.gl.eRadius,
            "color": self.gl.eCol,
            "draw_edges": self.gl.draw_edges,
        }

    @edge_props.setter
    def edge_props(self, props):
        """
        Specify the edges and set how they are drawn in OpenGL.

        Accepted is a dictionary with the following optional keys:
          - es,
          - radius,
          - color,
          - draw_edges.
        """
        if props:
            if "es" in props and props["es"] is not None:
                self.es = props["es"]
            if "radius" in props and props["radius"] is not None:
                self.gl.eRadius = props["radius"]
                self.gl.useCylinderEs = props["radius"] > 0.0
                if self.gl.useCylinderEs:
                    if self.gl.cyl is not None:
                        del self.gl.cyl
                    self.gl.cyl = Scenes3D.P2PCylinder(radius=props["radius"])
            if "color" in props and props["color"] is not None:
                self.gl.eCol = props["color"]
            if "draw_edges" in props and props["draw_edges"] is not None:
                self.gl.draw_edges = props["draw_edges"]

    def regen_edges(self):
        """
        Recreates the edges in the 3D object by using an adges for every side of
        a face, i.e. all faces will be surrounded by edges.

        Edges will be filtered so that shared edges between faces,
        i.e. edges that have the same vertex index, only appear once.
        The creation of edges is not optimised and can take a long time.
        """
        Es2D = []
        es = []

        def addEdge(i, j):
            if i < j:
                edge = [i, j]
            elif i > j:
                edge = [j, i]
            else:
                return
            if not edge in Es2D:
                Es2D.append(edge)
                es.extend(edge)

        for face in self.fs:
            lastIndex = len(face) - 1
            for i in range(lastIndex):
                addEdge(face[i], face[i + 1])
            # handle the edge from the last vertex to the first vertex separately
            # (instead of using % for every index)
            addEdge(face[lastIndex], face[0])
        self.es = es

    @property
    def face_props(self):
        """
        Return the current face properties.

        Returned is a dictionary with the keywords fs, colors, and draw_faces.
        fs: Optional array of faces, that do not need to be triangular. It is a
            hierarchical array, ie it consists of sub-array, where each
            sub-array describes one face. Each n-sided face is desribed by n
            indices. Empty on default. Using triangular faces only gives a
            better performance.
            If fs is None, then the previous specified value will be used.
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each face with
                   index 'i' in fs which colour index from the parameter color
                   is used for this face. If empty then colors[0][0] shall be
                   used for each face.
                   It should have the same length as fs (or the current faces if
                   fs not specified) otherwise the parameter is ignored and the
                   face colors are set by some default algorithm.
        draw_faces: settings that expresses whether the faces should be drawn.
        """
        return {"fs": self.fs, "colors": self._shape_colors, "draw_faces": self.gl.draw_faces}

    @face_props.setter
    def face_props(self, props):
        """
        Define the properties of the faces.

        Send in an dictionary with the following keys:
          - fs,
          - colors,
          - draw_faces.
        See getter for the explanation of the keys.
        """
        if props:
            if "fs" in props and props["fs"] is not None:
                self._set_faces(props["fs"])
            if "colors" in props and props["colors"] is not None:
                self.shape_colors = props["colors"]
            self.divideColorWrapper()
            if "draw_faces" in props and props["draw_faces"] is not None:
                self.setEnableDrawFaces(props["draw_faces"])

    @staticmethod
    def triangulate(faces):
        """Divide faces into triangles

        The faces aren't triangulated so that the triangles cover the same area. This is mainly done
        to use the stencil buffer for concave polygons.

        return: a new list with faces, but each face is replaced with one list with vertex indices,
        which would form triangles if they are grouped by three.
        """
        return [
            # i+1 before i, to keep clock-wise direction
            [t for i in range(1, len(f) - 1) for t in (f[0], f[i + 1], f[i])]
            for f in faces
        ]

    def _set_faces(self, fs):
        """
        Define the shape faces

        fs: same as in face_props.
        """
        for f in fs:
            assert len(f) > 2, "A face should have at least 3 vertices"
        self.fs = fs
        self.TriangulatedFs = self.triangulate(fs)
        self.no_of_fs = len(self.fs)
        self.face_normals_up_to_date = False
        # if you autogenerate the vertex normal, using the faces, you need to
        # regenerate by setting self.gl.updateVs
        self.gl.updateVs = self.generate_normals

    @property
    def shape_colors(self):
        """Get the color data for this shape (see colors @ __init__)."""
        return self._shape_colors

    @shape_colors.setter
    def shape_colors(self, colors):
        """Set the face colours.

        colors: same as in __init__
        """
        if colors[0] is not None:
            col_defs = colors[0]
        else:
            col_defs = self._shape_colors[0]
        if colors[1] is not None:
            face_cols = colors[1]
        else:
            face_cols = self._shape_colors[1]
        self._shape_colors = (col_defs, face_cols)
        self.no_of_cols = len(col_defs)
        self.colRange = range(self.no_of_cols)
        assert self.no_of_cols > 0, "Empty col_defs: %s" % col_defs

    def setEnableDrawFaces(self, draw=True):
        """
        Set whether the faces need to be drawn in gl_draw (or not).

        draw: optional argument that is True by default. Set to False to
              disable drawing of the faces.
        """
        self.gl.draw_faces = draw

    def generate_face_normal(self, f, normalise):
        l = len(f)
        assert l > 2, "An face should at least have 2 vertices"
        if l < 3:
            assert False, "Normal for digons not implemented"
            # TODO: what to do here?
        normal = Triangle(self.vs[f[0]], self.vs[f[1]], self.vs[f[2]]).normal(normalise)
        if self.normal_direction == TRI_OUT or self.normal_direction == TRI_IN:
            v0 = geomtypes.Vec3(self.vs[f[0]])
            outwards = v0.norm() < (v0 + normal).norm()
            if (outwards and self.normal_direction == TRI_IN) or (
                not outwards and self.normal_direction == TRI_OUT
            ):
                normal = -normal
        return normal

    def create_face_normals(self, normalise):
        """Create face normals and save in self.

        normalise: boolean stating whether to normalise the normals.

        return: none
        """
        # TODO use smarter sol than self.face_normals_len_1 != normalise:
        # if already normalised, you never need to recalc
        # if not yet normalised, but required, just normalise.
        if not self.face_normals_up_to_date or self.face_normals_len_1 != normalise:
            self.face_normals = [self.generate_face_normal(f, normalise) for f in self.fs]
            self.face_normals_up_to_date = True
            self.face_normals_len_1 = normalise

    def create_vertex_normals(self, normalise, vs=None):
        """Create vertex normals and save in self.

        vs: and array with vertices to create normals for. Is not set, then self.vs is used.
        normalise: boolean stating whether to normalise the normals.

        return: none
        """
        if vs is None:
            vs = self.vs
        self.create_face_normals(normalise)
        # only use a vertex once, since the normal can be different
        self.nVs = []
        self.vNs = []
        for face, normal in zip(self.fs, self.face_normals):
            self.vNs.extend([normal for vi in face])
            self.nVs.extend([[vs[vi][0], vs[vi][1], vs[vi][2]] for vi in face])
        self.createVertexNormals_vi = -1

        def inc():
            self.createVertexNormals_vi += 1
            return self.createVertexNormals_vi

        self.nFs = [[inc() for i in face] for face in self.fs]
        self.TriangulatedFs = self.triangulate(self.nFs)
        # Now for the edge vertices. Note that edge vertices aren't necessarily
        # part of the face vertices.
        edgeIndexOffset = len(self.nVs)
        self.nVs.extend(vs)
        if normalise:
            for v in vs:
                self.vNs.append(v.normalize())
        else:
            for v in vs:
                self.vNs.append(v)
        self.nEs = [oldVi + edgeIndexOffset for oldVi in self.es]

    def create_edge_lengths(self, precision=12):
        e2l = {}
        l2e = {}
        for ei in len(self.es):
            vi0 = self.es[ei]
            vi1 = self.es[ei + 1]
            if vi0 < vi1:
                t = (vi0, vi1)
            else:
                t = (vi1, vi0)
            l = (geomtypes.Vec3(self.vs[vi1]) - geomtypes.Vec3(self.vs[vi0])).norm()
            e2l[t] = l
            l = round(l, precision)
            try:
                l2e[l].append(t)
            except KeyError:
                l2e[l] = [t]
        self.e2l = e2l
        self.l2e = l2e
        return l2e

    def _get_dihedral_angles(self, precision=12):
        """Get all different dihedral angles.

        precision: number of decimals to take into account to interpret as unique angle

        return: a dictionary where the keys are the unique dihedral angles and the values are a list
        of edges, where each edge is a tuple with a pair of vertex indices.
        """
        self.create_face_normals(normalise=False)
        dihedral_to_edge = {}  # the result
        no_of_faces = len(self.fs)

        def add_dihedral_angle(face_idx, chk_face, cfi, edge, v0_chk_face_idx):
            """Add one dihedral angle to the global dihedral_to_edge

            face_idx: the index of the face under investigation
            chk_face: the face we are checking against holding a list of vertex indices
            cfi: the index of chk_face in the list of faces
            edge: an edge consisting of a pair vertex indices (in a tuple). The dihedral angle for
                this face will be added.
            v0_chk_face_idx: index of edge[0] in chk_face.

            return: None.
            """
            v0_idx, v1_idx = edge
            i_prev = v0_chk_face_idx - 1
            if i_prev < 0:
                i_prev = len(chk_face) - 1
            i_next = v0_chk_face_idx + 1
            if i_next >= len(chk_face):
                i_next = 0
            # if the vertex v0_idx - v1_idx is part of chk_face
            if chk_face[i_prev] == v1_idx or chk_face[i_next] == v1_idx:
                # found: add the angle and edge to dihedral_to_edge
                if v0_idx < v1_idx:
                    t = (v0_idx, v1_idx)
                else:
                    t = (v1_idx, v0_idx)
                angle = math.pi - self.face_normals[face_idx].angle(self.face_normals[cfi])
                angle = round(angle, precision)
                try:
                    dihedral_to_edge[angle].append(t)
                except KeyError:
                    dihedral_to_edge[angle] = [t]

        for face_idx, face in enumerate(self.fs):
            no_of_indices = len(face)
            for edge in [(v_idx, face[(i + 1) % no_of_indices]) for i, v_idx in enumerate(face)]:
                for next_face_idx in range(face_idx + 1, no_of_faces):
                    chk_face = self.fs[next_face_idx]
                    try:
                        i = chk_face.index(edge[0])
                    except ValueError:
                        i = -1
                    if i >= 0:
                        add_dihedral_angle(face_idx, chk_face, next_face_idx, edge, i)
        return dihedral_to_edge

    def divideColorWrapper(self):
        """
        Divide the specified colours over the faces.

        This function wraps the divideColor function and handles the trivial
        cases for which there is only one colour of for which there are more
        colours than faces. These trivial cases do not need to be implemented by
        every descendent.
        """
        if len(self._shape_colors[1]) != self.no_of_fs:
            if self.no_of_cols == 1:
                self._shape_colors = (self._shape_colors[0], [0 for i in range(self.no_of_fs)])
            elif self.no_of_cols < self.no_of_fs:
                self.divideColor()
            else:
                self._shape_colors = (self._shape_colors[0], list(range(self.no_of_fs)))
            assert len(self._shape_colors[1]) == self.no_of_fs
        # generate an array with Equal coloured faces:
        self.EqColFs = [[] for col in range(self.no_of_cols)]
        for i in range(self.no_of_fs):
            self.EqColFs[self._shape_colors[1][i]].append(i)

    def divideColor(self):
        """
        Divide the specified colours over the isometries.

        This function should actually be implemented by a descendent, so that
        the colours can be divided according to the symmetry. This function
        just repeats the colours until the length is long enough.
        The amount of colours should be less than the nr of isomentries.
        """
        div = self.no_of_fs // self.no_of_cols
        mod = self.no_of_fs % self.no_of_cols
        face_cols = []
        colorIRange = list(range(self.no_of_cols))
        for i in range(div):
            face_cols.extend(colorIRange)
        face_cols.extend(list(range(mod)))
        self._shape_colors = (self._shape_colors[0], face_cols)

    def transform(self, trans):
        """Transform the model using the specified instance of a geomtypes.Trans3 object."""
        self.vs = [trans * v for v in self.vs]
        self.gl.updateVs = True

    def scale(self, factor):
        """Scale the vertices of the object."""
        self.vs = [factor * v for v in self.vs]
        self.gl.updateVs = True

    def zoom(self, factor):
        """Use the specified factor to zoom in when drawing the 3D object.

        This is used for scaling polychora cells
        """
        self.zoom_factor = factor
        self.gl.updateVs = True

    def calculateFacesG(self):
        self.fGs = [
            reduce(lambda t, i: t + self.vs[i], f, VEC(0, 0, 0)) / len(f)
            for f in self.fs
        ]

    def calculateSphereRadii(self, precision=12):
        """Calculate the radii for the circumscribed, inscribed and mid sphere(s)"""
        # calculate the circumscribed spheres:
        self.spheresRadii = Fields()
        self.spheresRadii.precision = precision
        s = {}
        for v in self.vs:
            r = round(v.norm(), precision)
            try:
                cnt = s[r]
            except KeyError:
                cnt = 0
            s[r] = cnt + 1
        self.spheresRadii.circumscribed = s
        s = {}
        for i in range(0, len(self.es), 2):
            v = (self.vs[self.es[i]] + self.vs[self.es[i + 1]]) / 2
            r = round(v.norm(), precision)
            try:
                cnt = s[r]
            except KeyError:
                cnt = 0
            s[r] = cnt + 1
        self.spheresRadii.mid = s
        s = {}
        try:
            self.fGs
        except AttributeError:
            self.calculateFacesG()
        for g in self.fGs:
            r = round(g.norm(), precision)
            try:
                cnt = s[r]
            except KeyError:
                cnt = 0
            s[r] = cnt + 1
        self.spheresRadii.inscribed = s

    def gl_init(self):
        """
        Initialise OpenGL for specific shapes

        Enables a derivative to use some specific OpenGL settings needed for
        this shape. This function is called in gl_draw for the first time gl_draw
        is called.
        """
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glDisable(GL.GL_CULL_FACE)

        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_BLEND)

        self.gl_initialised = True

    def gl_draw(self):
        """wrap _gl_draw to be able to catch OpenGL errors"""
        if self.vs == []:
            return
        if not self.gl_initialised:
            self.gl_init()

        # Check if unity matrix?
        GL.glPushMatrix()

        try:
            self._gl_draw()
        except GL.OpenGL.error.Error:
            logging.error("OpenGL Error occurred. Did you define PYOPENGL_PLATFORM?")
        except:
            GL.glPopMatrix()
            raise

        GL.glPopMatrix()

    def _gl_draw(self):
        """
        Draw the base element according to the definition of the vs, es, fs and
        colour settings.

        Set self.vertex_props, and edge_props and face_props to specify how and whether to draw
        the vertices, edges and faces respectively.
        """
        GL.glMultMatrixd(self.orientation.glMatrix())
        if self.gl.updateVs:
            # calculate the gravitational centre. Only calculate the vertices
            # that are used:
            if geomtypes.FloatHandler.eq(self.zoom_factor, 1.0):
                vs = self.vs
            else:
                v_usage = glue.getVUsageIn1D(self.vs, self.es)
                v_usage = glue.getVUsageIn2D(self.vs, self.fs, v_usage)
                g = VEC(0, 0, 0)
                total = 0
                for v_idx in self.VsRange:
                    g = g + v_usage[v_idx] * geomtypes.Vec3(self.vs[v_idx])
                    total += v_usage[v_idx]
                if total != 0:
                    g = g / total
                vs = [self.zoom_factor * (geomtypes.Vec3(v) - g) + g for v in self.vs]

            # At least on Ubuntu 8.04 conversion is not needed
            # On windows and Ubuntu 9.10 the vs cannot be an array of vec3...
            if not self.generate_normals:
                try:
                    if not GL.glVertexPointerf(vs):
                        return
                    normals = self.ns
                except TypeError:
                    vs = [[v[0], v[1], v[2]] for v in vs]
                    logging.info("gl_draw: converting vs(ns); vec3 type not accepted")
                    if not GL.glVertexPointerf(vs):
                        return
                    normals = [[v[0], v[1], v[2]] for v in self.ns]
                if normals != []:
                    assert len(normals) == len(
                        vs
                    ), "the normal vector array 'normals' should have as many normals as vertices."
                    GL.glNormalPointerf(normals)
                    self.NsSaved = normals
                else:
                    GL.glNormalPointerf(vs)
                    self.NsSaved = vs
            elif self.ns != [] and len(self.ns) == len(vs):
                try:
                    if not GL.glVertexPointerf(vs):
                        return
                    normals = self.ns
                except TypeError:
                    vs = [[v[0], v[1], v[2]] for v in vs]
                    logging.info("gl_draw: converting vs(ns); vec3 type not accepted")
                    if not GL.glVertexPointerf(vs):
                        return
                    normals = [[n[0], n[1], n[2]] for n in self.ns]
                GL.glNormalPointerf(normals)
                self.NsSaved = normals
            else:
                self.create_vertex_normals(True, vs)
                if self.nVs != []:
                    if not GL.glVertexPointerf(self.nVs):
                        return
                GL.glNormalPointerf(self.vNs)
                self.NsSaved = self.vNs
                vs = self.nVs
            self.gl.updateVs = False
            self.VsSaved = vs
        else:
            if self.gl.alwaysSetVertices:
                if not GL.glVertexPointerf(self.VsSaved):
                    return
                GL.glNormalPointerf(self.NsSaved)
        # VERTICES
        if self.gl.addSphereVs:
            GL.glColor(self.gl.vCol[0], self.gl.vCol[1], self.gl.vCol[2])
            for i in self.VsRange:
                self.gl.sphere.draw(self.vs[i])
        # EDGES
        if self.gl.draw_edges:
            if self.generate_normals and (self.ns == [] or len(self.ns) != len(self.vs)):
                es = self.nEs
                vs = self.nVs
            else:
                es = self.es
                vs = self.vs
            GL.glColor(self.gl.eCol[0], self.gl.eCol[1], self.gl.eCol[2])
            if self.gl.useCylinderEs:
                # draw edges as cylinders
                for i in range(0, len(self.es), 2):
                    self.gl.cyl.draw(v0=vs[es[i]], v1=vs[es[i + 1]])
            else:
                # draw edges as lines
                GL.glPolygonOffset(1.0, 3.0)
                GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
                GL.glDrawElementsui(GL.GL_LINES, es)
                GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)

        # FACES
        if self.gl.draw_faces:
            for col_idx in self.colRange:
                c = self._shape_colors[0][col_idx]
                if len(c) == 3:
                    GL.glColor(c[0], c[1], c[2])
                else:
                    a = max(c[3], 0)
                    a = min(a, 1)
                    GL.glColor(c[0], c[1], c[2], a)
                for face_idx in self.EqColFs[col_idx]:
                    triangles = self.TriangulatedFs[face_idx]
                    # Note triangles is a flat (ie 1D) array
                    if len(triangles) == 3:
                        GL.glDrawElementsui(GL.GL_TRIANGLES, triangles)
                    else:
                        # TODO: This part belongs to a GLinit:
                        GL.glClearStencil(0)
                        stencil_bits = GL.glGetIntegerv(GL.GL_STENCIL_BITS)
                        assert (
                            stencil_bits > 0
                        ), "Only triangle faces are supported, since there is no stencil bit"
                        # << TODO: end part that belongs to a GLinit
                        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
                        # use stecil buffer to triangulate.
                        GL.glColorMask(
                            GL.GL_FALSE, GL.GL_FALSE, GL.GL_FALSE, GL.GL_FALSE
                        )
                        GL.glDepthMask(GL.GL_FALSE)
                        # Enable Stencil, always pass test
                        GL.glEnable(GL.GL_STENCIL_TEST)
                        # always pass stencil test
                        GL.glStencilFunc(GL.GL_ALWAYS, 1, 1)
                        # stencil fail: don't care, never fails
                        # z-fail: zero
                        # both pass: invert stencil values
                        GL.glStencilOp(GL.GL_KEEP, GL.GL_ZERO, GL.GL_INVERT)
                        # Create triangulated stencil:
                        GL.glDrawElementsui(GL.GL_TRIANGLES, triangles)
                        # Reset colour mask and depth settings.
                        GL.glDepthMask(GL.GL_TRUE)
                        GL.glColorMask(GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE)
                        # Draw only where stencil equals 1 (masked to 1)
                        # GL_INVERT was used, i.e. in case of e.g. 8 bits the value is
                        # either 0 or 0xff, but only the last bit is checked.
                        GL.glStencilFunc(GL.GL_EQUAL, 1, 1)
                        # make stencil read only:
                        GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)
                        # Now, write according to stencil
                        GL.glDrawElementsui(GL.GL_TRIANGLES, triangles)
                        # ready, disable stencil
                        GL.glDisable(GL.GL_STENCIL_TEST)

    def to_off(
        self, precision=geomtypes.FLOAT_OUT_PRECISION, info=False, color_floats=False
    ):
        """Return a representation of the object in the 3D 'OFF' file format.

        precision: the precision that will be used for printing the coordinates
                   of the vertices.
        color_floats: whether to export the colours as floating point numbers
                      between 0 and 1. If False an integer 0 to 255 is used.
        """
        w = lambda a: "{}{}\n".format(s, a)
        s = ""
        s = w("OFF")
        s = w("#")
        s = w(f"# {self.name}")
        s = w("#")
        s = w("# file generated with python script by Marcel Tunnissen")
        if info:
            self.calculateSphereRadii()
            s = w(f"# inscribed sphere(s)    : {self.spheresRadii.inscribed}")
            s = w(f"# mid sphere(s)          : {self.spheresRadii.mid}")
            s = w(f"# circumscribed sphere(s): {self.spheresRadii.circumscribed}")
            dihedral_to_angle = self._get_dihedral_angles()
            for a, es in dihedral_to_angle.items():
                s = w(
                    "# Dihedral angle: {} rad ({} degrees) for {} edges".format(
                        geomtypes.f2s(a, precision),
                        geomtypes.f2s(a * Rad2Deg, precision),
                        len(es),
                    )
                )
                if len(es) > 2:
                    s = w(f"#                 E.g. {es[0]}, {es[1]}, {es[2]} etc")
            l2e = self.create_edge_lengths()
            for l, es in l2e.items():
                s = w(f"# Length: {geomtypes.f2s(l, precision)} for {len(es)} edges")
                if len(es) > 2:
                    s = w(f"#         E.g. {es[0]}, {es[1]}, {es[2]}, etc")
        s = w("# Vertices Faces Edges")
        no_of_faces = len(self.fs)
        no_of_edges = len(self.es) // 2
        s = w(f"{len(self.vs)} {no_of_faces} {no_of_edges}")
        s = w("# Vertices")
        for V in self.vs:
            s = w(
                "{} {} {}".format(
                    geomtypes.f2s(V[0], precision),
                    geomtypes.f2s(V[1], precision),
                    geomtypes.f2s(V[2], precision),
                )
            )
        s = w("# Sides and colours")
        # self._shape_colors[1] = [] : use self._shape_colors[0][0]
        # self._shape_colors[1] = [c0, c1, .. cn] where ci is an index i
        #                     self._shape_colors[0]
        #                     There should be as many colours as faces.
        if len(self._shape_colors[0]) == 1:
            oneColor = True
            color = self._shape_colors[0][0]
        else:
            oneColor = False
            assert len(self._shape_colors[1]) == len(self.fs)

        def face_str(face):
            """convert face to string in off-format."""
            s = f"{len(face)} "
            for fi in face:
                s += f" {fi}"
            if color_floats:
                s += "  {:g} {:g} {:g}".format(color[0], color[1], color[2])
            else:
                s += "  {:d} {:d} {:d}".format(
                    int(color[0] * 255),
                    int(color[1] * 255),
                    int(color[2] * 255),
                )
            return s

        if oneColor:
            for face in self.fs:
                # the lambda w didn't work: (Ubuntu 9.10, python 2.5.2)
                s += f"{face_str(face)}\n"
        else:
            self.create_face_normals(normalise=True)
            for i in range(no_of_faces):
                face = self.fs[i]
                color = self._shape_colors[0][self._shape_colors[1][i]]
                # the lambda w didn't work: (Ubuntu 9.10, python 2.5.2)
                s = "%s%s\n" % (s, face_str(face))
                fnStr = "%s %s %s" % (
                    geomtypes.f2s(self.face_normals[i][0], precision),
                    geomtypes.f2s(self.face_normals[i][1], precision),
                    geomtypes.f2s(self.face_normals[i][2], precision),
                )
                if info:
                    s = w(f"# face normal: {fnStr}")
        if info:
            for i in range(no_of_edges):
                s = w("# edge: {:d} {:d}".format(self.es[2 * i], self.es[2 * i + 1]))
        s = w("# END")
        return s

    @staticmethod
    def _get_face_plane(vs, face):
        """
        Define a Plane object from a face

        vs: the 3D vertex coordinates
        face: the indices in vs that form the face.
        Returns None if the vertices do not define a plane.
        """
        assert len(face) > 2, "a face should at least be a triangle"
        plane = None
        plane_found = False
        fi_0 = 1
        fi_1 = 2
        while not plane_found:
            try:
                plane = Plane(vs[face[0]], vs[face[fi_0]], vs[face[fi_1]])
                plane_found = True
            except ValueError or AssertionError:
                fi_1 += 1
                if fi_1 >= len(face):
                    fi_0 += 1
                    fi_1 = fi_0 + 1
                    if fi_1 >= len(face):
                        logging.info("Ignoring degenerate face (line or point?)")
                        break
        return plane

    def _merge_faces_sharing_plane(self, face_indices):
        """Merge face lying in one plane to one compound of faces.

        Faces that don't share a plane will become a compound of one face

        face_indices: a list of face indices, where an index refers to self.fs

        return: a list for face compounds where each elements consists of two elements:
            1. a list of faces (where each face is a list for vertex indices)
            2. the plane (an object of class Plane) the face is lying in.
        """
        result = []

        # Calc all face planes and ignore "fake" faces:
        faces = []
        for i in face_indices:
            face = self.fs[i]
            face_plane = self._get_face_plane(self.vs, face)
            if face_plane is None:
                continue  # not a face
            if face_plane.N is None:
                continue  # not a face
            faces.append((face, face_plane))

        for face, plane in faces:
            found = False
            logging.debug("checking plane %s for face %s of len %d", plane, face, len(face))
            for existing_face_compound, existing_plane in result:
                if plane == existing_plane:
                    existing_face_compound.append(face)
                    logging.debug("FOUND")
                    found = True
                    break
            if not found:
                logging.debug("Adding new plane")
                result.append(([face], plane))
        return result

    def _rotate_shape_to_hor_plane(self, face_plane):
        """
        Rotate the vertices so that the specified plane is parallel to the XOY plane

        face_plane: an object of class Plane.

        return: a tuple with the updated shape vertices and the same vertices where the z-coordinate
        is removed.
        """
        # Find out how to rotate the shape such that the norm of the base face
        # is parallel to the z-axis to work with a 2D situation:
        # Rotate around the cross product of z-axis and norm
        # with an angle equal to the dot product of the normalised vectors.
        z_axis = VEC(0, 0, 1)
        to_2d_angle = geomtypes.RoundedFloat(math.acos(z_axis * face_plane.N))
        if (
            to_2d_angle == 2 * math.pi
            or to_2d_angle == -2 * math.pi
            or to_2d_angle == math.pi
            or to_2d_angle == -math.pi
        ):
            to_2d_angle = geomtypes.RoundedFloat(0.0)
        if to_2d_angle != 0:
            logging.debug("to_2d_angle: %f", to_2d_angle)
            to_2d_axis = face_plane.N.cross(z_axis)
            logging.debug("to_2d_axis: %s", to_2d_axis)
            rot_mat = geomtypes.Rot3(angle=to_2d_angle, axis=to_2d_axis)
            vs = [rot_mat * v for v in self.vs]
        else:
            vs = self.vs[:]

        return vs

    # TODO: Instead of face, vs perhaps you should just have a list of vertices for face
    def _calc_intersection(self, face, face_plane, hor_plane, z, vs):
        """Calculate the intersections for a face with a horizontal plane

        The result will consist of line segments that are part of the face. For a convex face there
        is only one segment, but for a concave there can be more than one.

        face: the face to intersect with the horizontal plane. It is a list of vertex indices.
        face_plane: the Plane object in which face is part of.
        hor_plane: the Plane object that defines the horizontal plane to intersect with.
        z: the z-coordinate for the horizontal plane.
        vs: the vertex indices as used for the face.

        return: a tuple with a Line2D object and a flat list of line factors that form line segments
            of where the face intersects the horizontal plane. Each segment is represen:ed by one
            pair of factors.
        """
        line_3d = hor_plane.intersect_with_plane(face_plane)
        if line_3d is None:
            logging.debug("No intersection for face")
        else:
            logging.debug("intersecting horizontal plane %s with %s", face_plane, line_3d)
            assert geomtypes.RoundedFloat(line_3d.v[2]) == 0, (
                "all intersection lines should be paralell to z = 0, "
                f"but z varies with {line_3d.v[2]} (margin: {FloatHandler.margin})"
            )
            assert geomtypes.RoundedFloat(line_3d.p[2]) == z, (
                f"all intersection lines should ly on z=={z}, "
                f"but z differs {z - line_3d.p[2]} "
                f"(margin: {FloatHandler.margin})"
            )

            line_2d = Line2D([line_3d.p[0], line_3d.p[1]], v=[line_3d.v[0], line_3d.v[1]])
            # now find the segment of line_2d within the face.
            # TODO The next call is strange. It is a call to a Line2D
            # intersecting a 3D facet. It should be a mode dedicated
            # call. The line is in the plane of the facet and we want to
            # know where it shares edges.
            line_factors = line_2d.intersect_with_face(vs, face, z)
            logging.debug("line factors %s", line_factors)
            if line_factors != []:
                return (line_2d, line_factors)
        return ()

    def _intersect_with_face_in_hor_plane(self, vs, compound_face, z):
        """
        Intersect all faces with a face in an horizontal plane

        vs: the list of vertices for an shape with an updated orientation so that the compound face
            is in a horizontal plane.
        comound_face: a list of faces. Each face is a list of vertex indices. The faces should all
            ly in the horizontal plane (with the orientatoin specified by vs)
        z: the z-value of the horizontal plane to intersect with.

        return: a tuple of a points list and a polygons list. Each point consists of an X, Y coordinate in the
            plane, while a polygon is a list of indinces in the points list. A polygon might also
            just be an egde.
        """
        hor_plane = PlaneFromNormal(VEC(0, 0, 1), VEC(0, 0, z))
        logging.debug("hor_plane %s", hor_plane)

        # split faces into
        # 1. faces that ly in the plane: faces_to_intersect_with, i.e. the other faces will be
        #    intersected with these.
        # 2. faces that share line segment(s) with this plane: intersection faces. Only save the
        #    line segments data of these.
        points = [[v[0], v[1]] for v in vs]
        polygons = []
        faces_to_intersect_with = []
        intersection_lines = []
        for intersecting_face in self.fs:
            logging.debug(
                "Intersecting face[%d] = %s with the compound face",
                self.fs.index(intersecting_face),
                intersecting_face,
            )
            intersecting_plane = self._get_face_plane(vs, intersecting_face)

            calc_intersection = True
            # check whether the intersection face is in the plane
            if intersecting_plane == hor_plane:
                faces_to_intersect_with.append(intersecting_face)
                polygons.append(intersecting_face)
                logging.debug("Intersecting face shares the plane")
                calc_intersection = False
            else:
                # Check whether they share an edge
                l = len(intersecting_face)
                for p in range(l):
                    for face in compound_face:
                        if intersecting_face[p] in face:
                            q = p + 1
                            if q == l:
                                q = 0
                            if intersecting_face[q] in face:
                                pIndex = face.index(intersecting_face[p])
                                qIndex = face.index(intersecting_face[q])
                                delta = abs(pIndex - qIndex)
                                if (delta == 1) or (delta == len(face) - 1):
                                    calc_intersection = False
                                    logging.debug("Intersecting face shares an edge")
                                    break

            # line of intersection:
            if calc_intersection:
                # TODO: I don't like this many parameters:
                intersection_line = self._calc_intersection(
                    intersecting_face, intersecting_plane, hor_plane, z, vs
                )
                if intersection_line:
                    intersection_lines.append(intersection_line)

        # for each intersecting line segment:
        for i, (line_2d, line_factors_0) in enumerate(intersection_lines):
            logging.debug("phase 2: check intersection %d", i)
            # line_2d: the line object representing the line of intersection
            # line_factors_0: the line segments (factors) valid for the intersecting face
            # line_factors_1: the line segments (factors) valid for the face to intersect with
            for face_to_intersect_with in faces_to_intersect_with:
                line_factors_1 = line_2d.intersect_with_face(vs, face_to_intersect_with, z)
                logging.debug("line_factors_1 %s", line_factors_1)
                # Now combine the results of line_factors_0 and line_factors_1:
                # Only keep intersections that fall within 2 segments for
                # both line_factors_0 and line_factors_1.
                facetSegmentNr = 0
                baseSegmentNr = 0
                nextBaseSeg = True
                nextFacetSeg = True
                no_of_points = len(points)

                def addPsLine(t0, t1, line_2d, no_of_points):
                    points.append(line_2d.getPoint(t0))
                    points.append(line_2d.getPoint(t1))
                    polygons.append([no_of_points, no_of_points + 1])
                    return no_of_points + 2

                while (baseSegmentNr < len(line_factors_1) // 2) and (
                    facetSegmentNr < len(line_factors_0) // 2
                ):
                    if nextBaseSeg:
                        b0 = geomtypes.RoundedFloat(line_factors_1[2 * baseSegmentNr])
                        b1 = geomtypes.RoundedFloat(line_factors_1[2 * baseSegmentNr + 1])
                        nextBaseSeg = False
                    if nextFacetSeg:
                        f0 = geomtypes.RoundedFloat(line_factors_0[2 * facetSegmentNr])
                        f1 = geomtypes.RoundedFloat(line_factors_0[2 * facetSegmentNr + 1])
                        nextFacetSeg = False
                    # Note that always holds f0 < f1 and b0 < b1
                    if f1 <= b0:
                        # f0 - f1  b0 - b1
                        nextFacetSeg = True
                    elif b1 <= f0:
                        # b0 - b1  f0 - f1
                        nextBaseSeg = True
                    elif f0 <= b0:
                        if f1 <= b1:
                            # f0  b0 - f1  b1
                            nextFacetSeg = True
                            no_of_points = addPsLine(b0, f1, line_2d, no_of_points)
                        else:
                            # f0  b0 - b1  f1
                            nextBaseSeg = True
                            no_of_points = addPsLine(b0, b1, line_2d, no_of_points)
                    else:
                        # b0<f0<b1 (and b0<f1)
                        if f1 <= b1:
                            # b0  f0 - f1  b1
                            nextFacetSeg = True
                            no_of_points = addPsLine(f0, f1, line_2d, no_of_points)
                        else:
                            # b0  f0 - b1  f1
                            nextBaseSeg = True
                            no_of_points = addPsLine(f0, b1, line_2d, no_of_points)
                    if nextBaseSeg:
                        baseSegmentNr += 1
                    if nextFacetSeg:
                        facetSegmentNr += 1

        return points, polygons

    def to_postscript(
        self,
        face_indices=None,
        scaling=1,
        precision=7,
        page_size=PS.PageSizeA4,
    ):
        """Print in PS For each face where the other faces meet that face.

        Returns a string in PS format that shows the pieces of faces that can
        be used for constructing a physical model of the object.

        The function will for each face check whether it intersects another
        face. By these intersections the face is divided into pieces. All pieces
        are printed, not only the ones that are visible from the outside.

        To get correct results and to prevent asserts it is wise to wrap this method in a
        FloatHandler statement as shown below. It shows an example of using 8 digits when comparing
        floats. Note this is independent of the precision parameter.
            with FloatHandler(precision=8):
                object.to_postscript(..)

        face_indices: an array of faces for which the pieces should be printed. Since many objects
            have symmetry it is not needed to calculate the pieces for each face.
        scaling: All pieces in all faces are scaled by a certain factor in the resulting PS string.
            This factor can be adjusted later in the file itself (after printing the string to a
            file).
        precision: The amount of decimals to use fir floating point numbers in the output string.
        """
        if not face_indices:
            face_indices = list(range(len(self.fs)))
        ps_doc = PS.doc(title=self.name, pageSize=page_size)
        if logging.root.level < logging.DEBUG:
            for i in range(len(self.vs)):
                logging.debug("V[%d] = %s", i, self.vs[i])

        compound_faces = self._merge_faces_sharing_plane(face_indices)

        for i, (compound_face, face_plane) in enumerate(compound_faces):
            logging.debug("checking face %d (of %d)", i + 1, len(compound_faces))

            vs = self._rotate_shape_to_hor_plane(face_plane)

            # set z-value for the z-plane, ie plane of intersection
            # TODO: better would be to take the average of all z coords
            z_base_plane = vs[compound_face[0][0]][2]
            logging.debug("z_base_face = %s", z_base_plane)

            points_2d, lines_to_draw = self._intersect_with_face_in_hor_plane(
                vs, compound_face, z_base_plane
            )

            ps_doc.addLineSegments(points_2d, lines_to_draw, scaling, precision)

        return ps_doc.toStr()

    def get_dome(self, level=2):
        """Change the shape towards into a dome shaped model

        This is done by calculating the outer sphere (through the vertices) and projecting parts of
        the shape from the middle onto this sphere.

        level: for level 1 the gravitation centre of each is projected on to the sphere; for level 2
        edge centres are mapped onto the sphere.
        """
        shape = None
        # check if level is in supported domain
        if level < 1 or level > 2:
            return shape
        cols = self.face_props["colors"]
        vs = self.vs[:]
        no_of_vs_org = len(self.vs)
        try:
            self.fGs
        except AttributeError:
            self.calculateFacesG()
        try:
            outer_radii = self.spheresRadii.circumscribed
        except AttributeError:
            self.calculateSphereRadii()
            outer_radii = self.spheresRadii.circumscribed
        radius = reduce(max, iter(outer_radii.keys()))
        fs = []
        col_indices = []

        def add_projected_vs(extra_vs):
            """Add extra vertices to the vertex array."""
            # func global vs, radius
            vs.extend([radius * x.normalize() for x in extra_vs])

        def dome_level_1(f, i):
            # return extra_fs
            # func global no_of_vs_org, cols
            # assumes that the gravity centres will be added to vs in face order
            # independently.
            l = len(f)
            return [[i + no_of_vs_org, f[j], f[(j + 1) % l]] for j in range(l)]

        def dome_level_2(f):
            # f can only be a triangle: no check
            # return (extra_vs, extra_fs) tuple
            # func global: vs
            extra_vs = []
            extra_vs = [(vs[f[i]] + vs[f[(i + 1) % 3]]) / 2 for i in range(3)]
            v_idx_offset = len(vs)
            extra_fs = [
                [v_idx_offset, v_idx_offset + 1, v_idx_offset + 2],
                [f[0], v_idx_offset, v_idx_offset + 2],
                [f[1], v_idx_offset + 1, v_idx_offset],
                [f[2], v_idx_offset + 2, v_idx_offset + 1],
            ]
            return (extra_vs, extra_fs)

        for i, f in enumerate(self.fs):
            if level == 1:
                extra_fs = dome_level_1(f, i)
                # add the gravity centres as assumed by dome_level_1:
                add_projected_vs(self.fGs)
            else:
                l = len(f)
                if l == 3:
                    extra_vs, extra_fs = dome_level_2(f)
                    add_projected_vs(extra_vs)
                elif l > 3:
                    tmp_fs = dome_level_1(f, i)
                    # add the gravity centres as assumed by dome_level_1:
                    add_projected_vs(self.fGs)
                    extra_fs = []
                    for sf in tmp_fs:
                        extra_vs, sxFs = dome_level_2(sf)
                        add_projected_vs(extra_vs)
                        extra_fs.extend(sxFs)
            fs.extend(extra_fs)
            col_indices.extend([cols[1][i] for j in range(len(extra_fs))])
        shape = SimpleShape(vs, fs, [], colors=(cols[0], col_indices))
        shape.regen_edges()
        return shape


class CompoundShape(base.Orbitit):
    """
    The class describes a shape that is the result of combining more than one
    SimpleShapes. The resulting shape can be treated as one, e.g. it can be
    exported as one 'OFF' file.
    """

    def __init__(
        self,
        shapes,
        regen_edges=True,
        name="CompoundShape",
    ):
        """
        shapes: a list of SimpleShape objects of which the shape is a compound.
        """
        self.name = name
        self.merge_needed = False
        # This is save so heirs can still use repr_dict from this class
        self.json_class = CompoundShape
        self.setShapes(shapes)
        if regen_edges:
            self.regen_edges()

    def __repr__(self):
        """
        Returns a python string that can be interpreted by Python for the shape
        """
        if len(self._shapes) == 1:
            return repr(self._shapes[0])
        s = indent.Str(
            "%s(\n" % base.find_module_class_name(self.__class__, __name__)
        )
        s = s.add_incr_line("shapes=[")
        s.incr()
        s = s.glue_line(
            ",\n".join(
                repr(shape).reindent(s.indent) for shape in self._shapes
            )
        )
        s = s.add_decr_line("],")
        s = s.add_line('name="%s"' % self.name)
        s = s.add_decr_line(")")
        if __name__ != "__main__":
            s = s.insert("%s." % __name__)
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        return {
            "class": base.class_to_json[self.json_class],
            "data": {
                "name": self.name,
                "shapes": [s.repr_dict for s in self.shapes],
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        return cls(
            shapes=[
                base.json_to_class[s["class"]].from_json_dict(s) for s in data["shapes"]
            ],
            name=data["name"],
        )

    def saveFile(self, fd):
        """
        Save a shape in a file descriptor

        The caller still need to close the filde descriptor afterwards
        """
        saveFile(fd, self)

    def add_shape(self, shape):
        """
        Add shape 'shape' to the current compound.
        """
        shape.gl.alwaysSetVertices = True
        self._shapes.append(shape)
        if len(self._shapes) > 1:
            self._shapes[-1].generate_normals = self._shapes[0].generate_normals
        self.merge_needed = True

    @property
    def shapes(self):
        return self._shapes

    def gl_alwaysSetVertices(self, do):
        for shape in self._shapes:
            shape.gl_alwaysSetVertices(do)

    def setShapes(self, shapes):
        """
        Set the shapes all at once.

        Note: you need to make sure yourself to have the generate_normals set
        consistently for all shapes.
        """
        self._shapes = shapes
        self.gl_alwaysSetVertices(True)
        self.merge_needed = True

    def merge_shapes(self):
        """Using the current array of shapes as defined in _shapes,
        initialise this object as a simple Shape.

        The function will create one vs, fs, and es from the current definition
        of _shapes and will initialise this object as a SimpleShape.
        """
        vs = []
        fs = []
        es = []
        ns = []
        col_defs = []
        colorIndices = []
        for s in self._shapes:
            VsOffset = len(vs)
            colOffset = len(col_defs)
            s = s.simple_shape
            # Apply shape orientation here, needed, since the can be different
            # for the various shapes
            for v in s.vs:
                vs.append(s.orientation * v)
            for v in s.ns:
                ns.append(s.orientation * v)
            # offset all faces:
            fs.extend([[i + VsOffset for i in f] for f in s.fs])
            es.extend([i + VsOffset for i in s.es])
            col_defs.extend(s.shape_colors[0])
            colorIndices.extend([i + colOffset for i in s.shape_colors[1]])
        self.merged_shape = SimpleShape(
            vs=vs, fs=fs, es=es, ns=ns, colors=(col_defs, colorIndices)
        )
        self.merge_needed = False

    @property
    def simple_shape(self):
        """Return the compound shape as a simple merged and flat shape"""
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape

    def clean_shape(self, precision):
        """Return a new shape for which vertices are merged and degenerated faces are deleted.

        The shape will not have any edges.

        precision: number of decimals to consider when deciding whether two floating point numbers
            are equal.
        """
        self.simple_shape.clean_shape(precision)

    def gl_draw(self):
        """Draws the compound shape as compound shape

        If you want to draw it as one, draw the SimpleShape instead
        """
        for shape in self._shapes:
            shape.gl_draw()

    def regen_edges(self):
        for shape in self._shapes:
            shape.regen_edges()
        self.merge_needed = True

    @property
    def vertex_props(self):
        """Return a dictionary of the vertex properties of the compound

        See setter what to expect.
        """
        # Note: cannot use the megedShape, since the vs is not an array of vs
        d = self._shapes[0].vertex_props
        return {
            "vs": self.vs,
            "radius": d["radius"],
            "color": d["color"],
            "ns": self.ns,
        }

    @vertex_props.setter
    def vertex_props(self, props):
        """Set the vertex properties for a whole compound shape at once

        The properties can be specified as a dictionary with the following keys:
        vs: This is an array of vs. One vs array for each shape element
        ns: This is an array of ns. One ns array for each shape element
        radius: one radius that is valid for all shape elements
        color: one vertex color that is valid for all shape elements

        See the same function in SimpleShape.
        """
        if props:
            if "vs" in props and props["vs"] is not None:
                vs = props["vs"]
            else:
                vs = [None for shape in self._shapes]
            if "ns" in props and props["ns"] is not None:
                ns = props["ns"]
            else:
                ns = [None for shape in self._shapes]
            if "radius" in props:
                radius = props["radius"]
            else:
                radius = None
            if "color" in props:
                color = props["color"]
            else:
                color = None
        assert len(vs) == len(self._shapes)
        assert len(ns) == len(self._shapes)
        for i in range(len(self._shapes)):
            self._shapes[i].vertex_props = {
                'vs': vs[i],
                'ns': ns[i],
                'radius': radius,
                'color': color,
            }
        self.merge_needed = True

    @property
    def edge_props(self):
        """Return a dictionary of the edge properties of the compound

        See setter what to expect.
        """
        d = self._shapes[0].edge_props
        return {
            "es": self.es,
            "radius": d["radius"],
            "color": d["color"],
            "draw_edges": d["draw_edges"],
        }

    @edge_props.setter
    def edge_props(self, props):
        """Set the edge properties for a whole compound shape at once

        Accepted is a dictionary with the following optional keys:
            es: This is an array of es. One es array for each shape element
            radius: one radius that is valid for all shape elements
            color: a list of colors (see SimpleShape.__init__). This list should contain an element
                for each shape.
            draw_edges: whether to draw the edges at all

        See the same function in SimpleShape.
        """
        if props:
            if "es" in props and props["es"] is not None:
                es = props["es"]
            else:
                es = [None for shape in self._shapes]
            if "radius" in props:
                radius = props["radius"]
            else:
                radius = None
            if "color" in props:
                color = props["color"]
            else:
                color = None
            if "draw_edges" in props:
                draw_edges = props["draw_edges"]
            else:
                draw_edges = None
        for i in range(len(self._shapes)):
            self._shapes[i].edge_props = {
                'es': es[i], 'radius': radius, 'color': color, 'draw_edges': draw_edges
            }
        self.merge_needed = True

    @property
    def face_props(self):
        """Return a dictionary of the face properties of the compound

        See face_props.setter what to expect.
        """
        d = self._shapes[0].face_props
        return {"fs": self.fs, "colors": self.shape_colors, "draw_faces": d["draw_faces"]}

    @face_props.setter
    def face_props(self, props):
        """Set the face properties for a whole compound shape at once

        Set to a dictionary with the following keys:
        fs: This is an array of es. One es array for each shape element
        colors: This is an array of colors. One colors set for each shape
                element.
        draw_faces: one draw_faces setting that is valid for all shape elements

        See the same function in SimpleShape.
        """
        if props:
            if "fs" in props and props["fs"] is not None:
                fs = props["fs"]
            else:
                fs = [None for shape in self._shapes]
            if "colors" in props and props["colors"] is not None:
                colors = props["colors"]
            else:
                colors = [None for shape in self._shapes]
            if "draw_faces" in props:
                draw_faces = props["draw_faces"]
            else:
                draw_faces = None
        for i, shape in enumerate(self._shapes):
            shape.face_props = {
                'fs': fs[i], 'colors': colors[i], 'draw_faces': draw_faces
            }
        self.merge_needed = True

    def transform(self, trans):
        """Transform the model using the specified instance of a geomtypes.Trans3 object."""
        for shape in self._shapes:
            shape.transform(trans)
        self.merge_needed = True

    def scale(self, factor):
        """Scale the vertices of the object."""
        for shape in self._shapes:
            shape.scale(factor)
        self.merge_needed = True

    @property
    def dimension(self):
        """The shapes dimension, normally 3."""
        return self._shapes[0].dimension

    @property
    def vs(self):
        """Return an array of shape vertices."""
        return [shape.vs for shape in self._shapes]

    @property
    def ns(self):
        """Return an array of shape (vertex) normals."""
        return [shape.ns for shape in self._shapes]

    @property
    def es(self):
        """Return an array of shape edges."""
        return [shape.es for shape in self._shapes]

    @property
    def fs(self):
        """Return an array of shape faces."""
        return [shape.fs for shape in self._shapes]

    @property
    def shape_colors(self):
        """Get the color settings for all shapes."""
        return [shape.shape_colors for shape in self._shapes]

    @property
    def generate_normals(self):
        """Boolean stating whether vertex normals need to be (re)generated."""
        return self._shapes[0].generate_normals

    def to_off(self, precision=geomtypes.FLOAT_OUT_PRECISION, info=False, color_floats=False):
        """Return a representation of the object in the 3D 'OFF' file format.

        See SimpleShape.to_off
        """
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.to_off(precision, info, color_floats)

    def to_postscript(
        self,
        face_indices=None,
        scaling=1,
        precision=7,
        page_size=PS.PageSizeA4,
    ):
        """Print in PS For each face where the other faces meet that face.

        Returns a string in PS format that shows the pieces of faces that can
        be used for constructing a physical model of the object.
        """
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.to_postscript(face_indices, scaling, precision, page_size)

    def get_dome(self, level=2):
        """Change the shape towards into a dome shaped model

        see SimpleShape.get_dome
        """
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.get_dome(level)


class SymmetricShape(CompoundShape):
    """
    The class describes simple shapes that have a base shape that is reused by
    some transformations. They can be expressed by a subset of all vertices,
    edges and faces. The isometries of the shape are then used to reproduce the
    complete shape.

    Colours can be specified for whole transformations of the base shape.
    """

    def __init__(
        self,
        vs,
        fs,
        es=None,
        ns=None,
        colors=None,
        isometries=None,
        regen_edges=True,
        orientation=None,
        name="SymmetricShape",
    ):
        """
        vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by gl_draw
        colors: optional array parameter describing the colours. Each element consists of RGB
            channel values (between 0 and 1). There should be an RGB value for each isometry..
        isometries: a list of all isometries that are needed to reproduce all
            parts of the shape can can be transformed from the specified base
            element through an isometry.
        regen_edges: if set to True then the shape will recreate the edges for all faces, i.e. all
            faces will be surrounded by edges. Edges will be filtered so that shared edges between
            faces, i.e. edges that have the same vertex index, only appear once. The creation of
            edges is not optimised and can take a long time.
        orientation: orientation of the base shape. This is an isometry operation.
        name: a string identifier representing the model.
        """
        # this is before creating the base shape, since it check "colors"
        self.base_shape = SimpleShape(
            vs,
            fs,
            es,
            ns=ns,
            colors=([colors[0]], []) if colors else None,
            orientation=orientation,
        )
        if regen_edges:
            self.base_shape.regen_edges()
        super().__init__([self.base_shape], name=name)
        # This is save so heirs can still use repr_dict from this class
        self.json_class = SymmetricShape
        self.shape_colors = colors
        self.isometries = isometries if isometries else [E]
        self.order = len(isometries)
        self.needs_apply_isoms = True
        self.show_base_only = False

    def __repr__(self):
        # comment out class name, see comment at __fix_repr__ below:
        # s = indent.Str('%s(\n' % base.find_module_class_name(self.__class__, __name__))
        s = indent.Str("SymmetricShape(\n")
        s = s.add_incr_line("vs=[")
        s.incr()
        try:
            s = s.glue_line(
                ",\n".join(
                    indent.Str(repr(v)).reindent(s.indent) for v in self.base_shape.vs
                )
            )
        except AttributeError:
            logging.error("Are you sure the vertices are all of type geomtypes.Vec3?")
            raise
        s = s.add_decr_line("],")
        s = s.add_line("fs=[")
        s.incr()
        s = s.glue_line(
            ",\n".join(
                indent.Str(repr(f)).reindent(s.indent) for f in self.base_shape.fs
            )
        )
        s = s.add_decr_line("],")
        if self.base_shape.es != []:
            s = s.add_line("es=%s," % repr(self.base_shape.es))
        if self.base_shape.ns != []:
            s = s.add_incr_line("ns=[")
            s.incr()
            try:
                s = s.glue_line(
                    ",\n".join(repr(n).reindent(s.indent) for n in self.base_shape.ns)
                )
            except AttributeError:
                logging.error(
                    "Are you sure the normals are all of type geomtypes.Vec3?"
                )
                raise
            s = s.add_decr_line("],")
        s = s.add_line("colors=[")
        s.incr()
        cols = self._shape_colors
        s = s.glue_line(
            ",\n".join(indent.Str(repr(c)).reindent(s.indent) for c in cols)
        )
        s = s.add_decr_line("],")
        if self.isometries is not None:
            s = s.add_line("isometries=[")
            s.incr()
            s = s.glue_line(
                ",\n".join(
                    indent.Str(repr(i)).reindent(s.indent) for i in self.isometries
                )
            )
            s = s.add_decr_line("],")
        s = s.add_line("name='%s'," % self.name)
        s = s.glue_line(
            indent.Str("orientation=%s" % repr(self.base_shape.orientation)).reindent(
                s.indent
            )
        )
        s = s.add_decr_line(")")
        if __name__ != "__main__":
            s = s.insert("%s." % __name__)
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        # Note that orientation IS essential here.
        return {
            "class": base.class_to_json[self.json_class],
            "data": {
                "name": self.name,
                "vs": self.base_shape.vs,
                "fs": self.base_shape.fs,
                "cols": self._shape_colors,
                "orientation": self.base_shape.orientation.repr_dict,
                "isometries": [i.repr_dict for i in self.isometries],
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        o = data["orientation"]
        return cls(
            data["vs"],
            data["fs"],
            isometries=[
                base.json_to_class[s["class"]].from_json_dict(s)
                for s in data["isometries"]
            ],
            colors=data["cols"],
            orientation=base.json_to_class[o["class"]].from_json_dict(o),
            name=data["name"],
        )

    def merge_shapes(self):
        if self.show_base_only:
            # assuming that the base shape is a simple shape:
            self.merged_shape = self.base_shape
            self.merge_needed = False
        elif self.needs_apply_isoms:
            self.apply_isoms()

        super().merge_shapes()

    @staticmethod
    def _chk_face_colors_par(colors):
        """Check whether the colors parameters is valid.

        If not raise an assert.

        return the default colours (useful if default colors are used)
        """
        if not colors:
            colors = [rgb.gray95[:]]
        else:
            assert len(colors) > 0, "colors should have at least one element"
            col0 = colors[0]
            if isinstance(col0, (float, int)):
                # one colour specified for all
                assert len(colors) == 3 or len(colors) == 4, f"Expected RGB(A), got {colors}"
                colors = [colors]
            else:
                # several colours specified
                assert isinstance(col0, (list, tuple)), (
                    f"expected first colour to be an RGB(A) value, got {col0}"
                )
        return colors

    @property
    def shape_colors(self):
        """Get the color data for this shape (see colors @ __init__)."""
        return self._shape_colors

    @shape_colors.setter
    def shape_colors(self, colors):
        """Check and set the face colours and and save their properties."""
        colors = self._chk_face_colors_par(colors)
        self._shape_colors = colors
        self.merge_needed = True
        self.needs_apply_isoms = True

    def apply_colors(self):
        """
        Divide the shape colors over the isometries and re-assign class field.
        """
        no_of_cols = len(self._shape_colors)
        if no_of_cols != self.order:
            if no_of_cols == 1:
                col_data_per_shape = [self._shape_colors[0] for i in range(self.order)]
            elif no_of_cols < self.order:
                div = self.order // no_of_cols
                mod = self.order % no_of_cols
                col_data_per_shape = []
                for _ in range(div):
                    col_data_per_shape.extend(self._shape_colors)
                col_data_per_shape.extend(self._shape_colors[:mod])
            else:
                col_data_per_shape = (self._shape_colors[: self.order],)
            self._shape_colors = col_data_per_shape
            no_of_cols = len(self._shape_colors)
        # else: nothing to update
        assert no_of_cols == self.order, f"{no_of_cols} != {self.order}"

    def apply_isoms(self):
        """
        Apply the isometry operations for the current properties, like vs and
        colour settings.

        This will create all the individual shapes.
        """
        if len(self._shape_colors) != self.order:
            self.apply_colors()
        shapes = [
            SimpleShape(
                self.base_shape.vs,
                self.base_shape.fs,
                self.base_shape.es,
                ns=self.base_shape.ns,
                colors=([self._shape_colors[i]], []),
                orientation=isom * self.base_shape.orientation,
            )
            for i, isom in enumerate(self.isometries)
        ]
        self.setShapes(shapes)
        self.needs_apply_isoms = False

    @property
    def base_vs(self):
        """Get the vertices of the base shape."""
        return self.base_shape.vs

    @base_vs.setter
    def base_vs(self, vs):
        """Set the vertices of the base shape.

        This will make sure that the necessary updates are made when needed.
        """
        assert len(vs) == len(self.base_shape.vs)
        self.base_shape.vertex_props = {'vs': vs}
        self.merge_needed = True
        self.needs_apply_isoms = True

    @property
    def orientation(self):
        """Get the base shape orientation."""
        return self.base_shape.orientation

    @orientation.setter
    def orientation(self, orientation):
        """Set the base shape orientation."""
        self.base_shape.orientation = orientation
        self.needs_apply_isoms = True

    @property
    def base_fs_props(self):
        """Get the face properties for the base_shape."""
        props = self.base_shape.face_props
        return {
            "fs": props["fs"],
            "colors": self._shape_colors[0],
            "draw_faces": self.props["draw_faces"],
        }

    @base_fs_props.setter
    def base_fs_props(self, props):
        """
        Define the properties of the faces for the base element.

        Accepted are the optional (keyword) parameters:
          - fs,
          - colors: see setter of shape_colors
          - colors: one RGB value (tuple / list) or a list of RGB values.
          - draw_faces.
        Check SimpleShape.face_props for more details.
        """
        if props:
            if "fs" in props and props["fs"] is not None:
                self.base_shape.face_props = {'fs': props["fs"]}
                self.needs_apply_isoms = True
            if "colors" in props and props["colors"] is not None:
                self.shape_colors = props["colors"]
                self.merge_needed = True
            if "draw_faces" in props and props["draw_faces"] is not None:
                self.base_shape.setEnableDrawFaces(props["draw_faces"])

    def transform(self, trans):
        """Transform the model using the specified instance of a geomtypes.Trans3 object."""
        def adjust_transform(isom):
            """Adjust the transform to global trans so the same result is obtained"""
            if isom.is_rot():
                return geomtypes.Rot3(angle=isom.angle(), axis=trans * isom.axis())
            if isom.is_rot_inv():
                return geomtypes.RotInv3(angle=isom.angle(), axis=trans * isom.axis())
            # reflection
            return geomtypes.Refl3(normal=trans * isom.plane_normal())

        self.isometries = [adjust_transform(isom) for isom in self.isometries]
        self.orientation = trans * self.orientation
        self.needs_apply_isoms = True

    def scale(self, factor):
        """Scale the vertices of the object."""
        self.base_shape.scale(factor)
        self.needs_apply_isoms = True

    def gl_draw(self):
        if self.show_base_only:
            self.base_shape.gl_draw()
        else:
            if self.needs_apply_isoms:
                self.apply_isoms()
            CompoundShape.gl_draw(self)

    def to_postscript(
        self,
        face_indices=None,
        scaling=1,
        precision=7,
        page_size=PS.PageSizeA4,
    ):
        """Print in PS For each face where the other faces meet that face.

        Returns a string in PS format that shows the pieces of faces that can
        be used for constructing a physical model of the object.
        """
        if self.merge_needed:
            self.merge_shapes()
        if not face_indices:
            # no need to print all faces in orbited, because of symmetry
            face_indices = list(range(len(self.base_shape.fs)))
        return self.simple_shape.to_postscript(
            face_indices, scaling, precision, page_size
        )


class SymmetricShapeSplitCols(SymmetricShape):
    """
    Same as a symmetric shape except that one can define a colour for each individual face.

    For this one shape_colors should be a color argument as in SimpleShape.__init__. which will be
    divided regularly over the symmetries. Optionally send in a list of these, where each element
    should be valid for each symmetry.
    """

    @staticmethod
    def _chk_face_colors_par(colors):
        """Check whether the colors parameters is valid.

        If not raise an assert.
        """
        if not colors:
            colors = [([rgb.gray95[:]], [])]
        assert len(colors) > 0, "colors should have at least one element"
        if isinstance(colors, tuple) or len(colors) == 2:
            colors = [colors]
        for c in colors:
            assert (
                len(c) == 2
            ), f"a colors element should be a 2-tuple (colors, face_i), got {c}"
        return colors

    def apply_isoms(self):
        """
        Apply the isometry operations for the current properties, like vs and
        colour settings.

        This will create all the individual shapes.
        """
        if len(self._shape_colors) != self.order:
            self.apply_colors()
        shapes = [
            SimpleShape(
                self.base_shape.vs,
                self.base_shape.fs,
                self.base_shape.es,
                ns=self.base_shape.ns,
                colors=self._shape_colors[i],
                orientation=isom * self.base_shape.orientation,
            )
            for i, isom in enumerate(self.isometries)
        ]
        self.setShapes(shapes)
        self.needs_apply_isoms = False


class OrbitShape(SymmetricShape):
    """
    The class describes simple shapes that are symmetric. They can be expressed
    by a subset of all vertices, edges and faces. The symmetry of the shape is
    then used to reproduce the complete shape. To be able to know how to
    reproduce the shape one needs to know the symmetry of the complete shape and
    one needs to know which symmetry group the of the specified subset is. The
    later is called stabiliser in group algebra.
    From these two one can derive which isometries are needed to reproduce the
    complete shape.
    """

    def __init__(
        self,
        vs,
        fs,
        es=None,
        ns=None,
        final_sym=isometry.E,
        stab_sym=isometry.E,
        colors=None,
        regen_edges=True,
        name="OrbitShape",
        quiet=False,
    ):
        """
        vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by gl_draw
        final_sym: the resulting symmetry of the shape.
        stab_sym: the symmetry of the stabiliser, which is a subgroup of final_sym
        colors: optional array parameter describing the colours. Each element consists of RGB
            channel values (between 0 and 1). There should be an RGB value for each isometry..
        regen_edges: if set to True then the shape will recreate the edges for all faces, i.e. all
            faces will be surrounded by edges. Edges will be filtered so that shared edges between
            faces, i.e. edges that have the same vertex index, only appear once. The creation of
            edges is not optimised and can take a long time.
        name: a string identifier representing the model.

        As an example: a square is used to define a cube. The square has a D4C4
        symmetry and the cube S4xI. The former is used as stab_sym and the latter
        as final_sym.
        The following parameters can be used:
        with v = lambda x, y, z: geomtypes.Vec3([x, y, z])
        vs = [v(1, 1, 1), v(1, -1, 1), v(1, -1, -1), v(1, 1, -1)] and
        fs = [[0, 1, 2, 3]]
        final_sym = S4xI(setup = {'o4axis0': v(0, 0, 1), 'o4axis1': v(0, 1, 0)})
        stab_sym = D4C4(setup = {'axis_n': v(1, 0, 0), 'normal_r': v(0, 1, 0)})
        colors: the colours per isometry. (use [] for none)
        """
        try:
            fs_quotient_set = final_sym / stab_sym
        except isometry.ImproperSubgroupError:
            logging.error("Stabiliser not a subgroup of final symmetry")
            raise
        len_f = len(final_sym)
        len_s = len(stab_sym)
        len_q = len(fs_quotient_set)
        assert len_f % len_s == 0, f"Expected divisable group length {len_f} / {len_s}"
        # assert len_q == len_f // len_s,\
        #    f"Wrong length ({len_q} != {len_f // len_s}) of quotient set (increase precisio?)"
        fs_orbit = [coset.get_one() for coset in fs_quotient_set]
        if not quiet:
            logging.info("Applying an orbit of order %d", len(fs_orbit))
        super().__init__(
            vs, fs, es, ns, isometries=fs_orbit, name=name, regen_edges=regen_edges
        )
        # This is save so heirs can still use repr_dict from this class
        self.json_class = OrbitShape
        self.final_sym = final_sym
        self.stab_sym = stab_sym
        if colors != []:
            self.shape_colors = colors

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        return {
            "class": base.class_to_json[self.json_class],
            "data": {
                "name": self.name,
                "vs": self.base_shape.vs,
                "fs": self.base_shape.fs,
                "cols": self._shape_colors,
                "final_sym": self.final_sym.repr_dict,
                "stab_sym": self.stab_sym.repr_dict,
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        return cls(
            data["vs"],
            data["fs"],
            final_sym=isometry.Set.from_json_dict(data["final_sym"]),
            stab_sym=isometry.Set.from_json_dict(data["stab_sym"]),
            colors=data["cols"],
            name=data["name"],
        )

    def __repr__(self):
        # This repr should be fixed, since you cannot be sure in which order the
        # isometry operation will be printed (there is no ordering in a Set.
        # This requires a more user friendly class interface for the user:
        # provide an array of colours and a symmetry (and index) on which the
        # colouring is based. For now fall back on the parental repr.
        s = indent.Str(f"{base.find_module_class_name(self.__class__, __name__)}(\n")
        s = s.add_incr_line("vs=[")
        s.incr()
        try:
            s = s.glue_line(
                ",\n".join(
                    indent.Str(repr(v)).reindent(s.indent) for v in self.base_shape.vs
                )
            )
        except AttributeError:
            logging.error("Are you sure the vertices are all of type geomtypes.Vec3?")
            raise
        s = s.add_decr_line("],")
        s = s.add_line("fs=[")
        s.incr()
        s = s.glue_line(
            ",\n".join(
                indent.Str(repr(f)).reindent(s.indent) for f in self.base_shape.fs
            )
        )
        s = s.add_decr_line("],")
        if self.base_shape.es != []:
            s = s.add_line("es=%s," % repr(self.base_shape.es))
        if self.base_shape.ns != []:
            s = s.add_incr_line("ns=[")
            s.incr()
            try:
                s = s.glue_line(
                    ",\n".join(repr(n).reindent(s.indent) for n in self.base_shape.ns)
                )
            except AttributeError:
                logging.error(
                    "Are you sure the normals are all of type geomtypes.Vec3?"
                )
                raise
            s = s.add_decr_line("],")
        s = s.add_line("colors=[")
        s.incr()
        cols = self._shape_colors
        s = s.glue_line(
            ",\n".join(indent.Str(repr(c)).reindent(s.indent) for c in cols)
        )
        s = s.add_decr_line("],")
        s = s.add_line("final_sym=")
        s.incr()
        s = s.glue_line((repr(self.final_sym) + ",").reindent(s.indent))
        s.decr()
        s = s.add_line("stab_sym=")
        s.incr()
        s = s.glue_line((repr(self.stab_sym) + ",").reindent(s.indent))
        s.decr()
        s = s.add_line("name='%s'," % self.name)
        s = s.add_decr_line(")")
        if __name__ != "__main__":
            s = s.insert("%s." % __name__)
        return s

    def set_cols(self, colours, stab_sym):
        """
        Use the colours as specied and divide them according stab_sym

        colours: an array with rgb colour defs.
        stab_sym: the colours will be divided in a symmetric way, ie. in such a way that the base
            parts with the same colour have the symmetry stab_sym. For this to happen:
                1. the following is required:
                   - stab_sym is a subgroup of final_sym at object creation.
                2. the following is usually the case:

            An example of the usual case. A square is used to define a cube as explained in
            __init__. former is used as stab_sym at object creation and the latter as final_sym.
            CONTINUE here: testing cube example.., really need to read a Scene...
        """


class Scene(ABC):
    """
    Used for creating scenes in the PolyhedraBrowser.

    To implement a scene one typically needs to do the following:
    1. implement a class derived from geom_3d.SimpleShape
    2. implement a class derived from a wx.Frame window that controls the layout
       of a shape object from step 1.
    3. implement a scene class derived from this class as follows:
       class MyScene(geom_3d.Scene):
           def __init__(self, parent, canvas):
               geom_3d.Scene.__init__(self, MyShape, MyCtrlWin, parent, canvas)
       where MyShape is the class from step 1 and MyCtrlWin is the class from
       step 2.
    """

    def __init__(self, ShapeClass, CtrlWinClass, parent, canvas):
        """Create an object of the Scene class

        ShapeClass: a class derived from geom_3d.SimpleShape
        CtrlWineClass: a class derived from wx.Frame implementing controls to
                       change the properties of the shape dynamically.
        parent: the main window of the application.
        canvas: the canvas on which the shape is supposed to be drawn with
                OpenGL.
        """
        self.shape = ShapeClass()
        self.ctrl_win = CtrlWinClass(self.shape, canvas, parent, wx.ID_ANY)

    def close(self):
        """Close the current scene and destroy all its widgets"""
        try:
            self.ctrl_win.Close(True)
        except RuntimeError:
            # The user probably closed the window already
            pass


# Classes that support conversion from and to JSON:
base.class_to_json[SimpleShape] = "shape"
base.class_to_json[CompoundShape] = "compound_shape"
base.class_to_json[SymmetricShape] = "symmetric_shape"
base.class_to_json[OrbitShape] = "orbit_shape"
base.json_to_class["shape"] = SimpleShape
base.json_to_class["compound_shape"] = CompoundShape
base.json_to_class["symmetric_shape"] = SymmetricShape
base.json_to_class["orbit_shape"] = OrbitShape