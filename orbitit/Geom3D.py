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
#------------------------------------------------------------------


import copy
import math
import wx
import sys
import os

from OpenGL import GL
from functools import reduce

from orbitit import base, geomtypes, glue, indent, isometry, PS, rgb, Scenes3D, X3D

# TODO:
# - Test the gl stuf of SimpleShape: create an Interactive3DCanvas
#   the Symmetry stuff should not contain any shape stuff
# - In SimpleShape I split the setFaceProperties in functions that set separate
#   properties. Do something similar for Edges and Vertices.
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
# - function toPsPiecesStr finds intersection: this should be part of a separate
#   functons mapping the SimpleShape on a shape consisting of none intersecting
#   pieces. This could be a child of SimpleShape.
# - add function to filter out vertices that ly within a certain area: these
#   should be projected on the avg of all of them: use a counter for this.
# - clean up a bit: some functions return objects, other return the strings.
#   Compare e.g. toOffStr, toX3dDoc. This is mainly since there are no Off
#   objects. But if you compare toPsPiecesStr, it returns a str, but there are
#   PS objects.

# Done
# - edges after reading off file

vec = lambda x, y, z: geomtypes.Vec3([x, y, z])

E = geomtypes.E     # Identity
I = geomtypes.I     # Central inversion

# constant that have deal with angles
Rad2Deg = 180.0/math.pi
Deg2Rad = math.pi/180
R1_2 = math.pi      # 1/2 of a circle

R1_3 = 2*math.pi/3  # 1/3 of a circle
R2_3 = 2*R1_3       # 2/3 of a circle

R1_4 = math.pi/2    # 1/4 of a circle
R3_4 = 3*R1_4       # 3/4 of a circle

R1_5 = 2*math.pi/5  # 1/5 of a circle
R2_5 = 2*R1_5       # 2/5 of a circle
R3_5 = 3*R1_5       # 3/5 of a circle
R4_5 = 4*R1_5       # 4/5 of a circle

V2 = math.sqrt(2)
V3 = math.sqrt(3)
V5 = math.sqrt(5)

defaultFloatMargin = 1.0e-15

def eq(a, b, margin = defaultFloatMargin):
    """
    Check if 2 floats 'a' and 'b' are close enough to be called equal.

    a: a floating point number.
    b: a floating point number.
    margin: if |a - b| < margin then the floats will be considered equal and
            True is returned.
    """
    return abs(a - b) < margin

# rm with cgtypes dependency
def Veq(Va, Vb, margin = defaultFloatMargin, d = 3):
    """
    Check if 2 'd' dimensional floating point vectors 'Va' and 'Vb' are close
    enough to be called equal.

    Va: a floating point number.
    Vb: a floating point number.
    margin: The function returns True if all elements ly within a margin of each
            other. I.e. the maximum distance for vectors to be called equal is
             ____________           ___
            V d*margin^2  = margin*V d
    d: optional dimension, 3 on default
    """
    result = True
    for i in range(d):
        result = result and eq(Va[i], Vb[i], margin)
    return result

def readPyFile(fd, recreateEdges = True):
    """Reads an the python file a 3D shape and returns an instance of that class

    fd: the file descriptor of a file that is opened with read permissions.
    return: an object of the SimpleShape class.
    """
    ed = {'__name__': 'readPyFile'}
    exec(fd.read(), ed)
    shape = ed['shape']
    if recreateEdges and len(shape.Es) == 0:
        shape.recreateEdges()
    return shape

def isInt(str):
    try:
        num = int(str)
        return True
    except ValueError:
        return False

def readOffFile(fd, recreateEdges = True, name = ''):
    """Reads an the std 'off' format of a 3D object and returns an object of the
    SimpleShape class.

    fd: the file descriptor of a file that is opened with read permissions.
    recreateEdges: if set to True then the SimpleShape will recreate the edges
                   for all faces, i.e. all faces will be surrounded by edges.
                   Edges will be filtered so that shared edges between faces,
                   i.e. edges that have the same vertex index, only appear once.
                   The creation of edges is not optimised and can take a long time.
    return: an object of the SimpleShape class.
    """
    states = {'checkOff': 0, 'readSizes': 1, 'readVs': 2, 'readFs': 3, 'readOk': 4}
    nrOfVs = 0
    nrOfFs = 0
    nrOfEs = 0
    Es = []
    i = 0
    # A dictionary where the key and value pairs are exchanged, for debugging
    # purposes:
    statesRev   = {}
    for (key, value) in states.items():
        statesRev[value] = key
    state = states['checkOff']
    debug = True
    debug = False
    vRadius = 0
    eRadius = 0
    for line in fd:
        words = line.split()
        if len(words) > 0 and words[0][0] != '#':
            if state == states['checkOff']:
                if words[0] == 'OFF':
                    state = states['readSizes']
                else:
                    break
                if debug: print('OFF file format recognised')
            elif state == states['readSizes']:
                # the function assumes: no comments in beween the 3 nrs
                assert words[0].isdigit()
                assert words[1].isdigit()
                assert words[2].isdigit()
                nrOfVs = int(words[0])
                nrOfFs = int(words[1])
                nrOfEs = int(words[2])
                # Dont check Euler: in a compound for each part F + V - E = 2
                # So the difference 2 becomes 2n for a compound of n.
                #assert nrOfEs + 2 == nrOfFs + nrOfVs
                state = states['readVs']
                Vs = []
                if debug: print('will read', nrOfVs, 'Vs', nrOfFs, 'Fs (', nrOfEs, 'edges)')
            elif state == states['readVs']:
                # the function assumes: no comments in beween (x, y, z) of Vs
                Vs.append(geomtypes.Vec3(words[0:3]))
                if debug: print('V[%d] =' % i,  Vs[-1])
                i = i + 1
                if i == nrOfVs:
                    state = states['readFs']
                    Fs = []
                    cols = []
                    fColors = [i for i in range(nrOfFs)]
                    i = 0
                    if nrOfFs == 0:
                        state = states['readOk']
                        print('Note: the OFF file only contains vertices')
                        vRadius = 0.05
            elif state == states['readFs']:
                # the function assumes: no comments in beween "q i0 .. iq-1 r g b"
                assert words[0].isdigit(), "error interpreting line as face {}".format(words)
                lenF = int(words[0])
                if lenF > 0:
                    assert (len(words) >= lenF + 4 or len(words) == lenF + 1)
                    face = [int(words[j]) for j in range(1, lenF + 1)]
                    if lenF >= 3:
                        Fs.append(face)
                        if len(words) == lenF + 1:
                            cols.append([0.8, 0.8, 0.8])
                        else:
                            if isInt(words[lenF+1]):
                                cols.append(
                                    [float(words[j])/255 for j in range(lenF+1, lenF+4)]
                                )
                            else:
                                cols.append(
                                    [float(words[j]) for j in range(lenF+1, lenF+4)]
                                )
                        if debug: print('face[%d] =' % i,  Fs[-1])
                        if debug: print('col[%d] =' % i,  cols[-1])
                    else:
                        if lenF == 2:
                            # this is an edge really...
                            Es.extend(face)
                            eRadius = 0.15
                            if debug: print('face[%d] =' % i,  face, '( = an edge)')
                            # what about different edge colours?
                        else:
                            # since vertices are defined explicitely, show them
                            vRadius = 0.05
                            print('Note: ignoring face %d with only %d vertices' % (
                                i, lenF
                            ))
                    i = i + 1
                    if i == nrOfFs:
                        state = states['readOk']
                        break;
            else:
                break
    assert state == states['readOk'], """
        EOF occurred while not done reading:
            Would read %d Vs and %d Fs;
            current state %s with %d items read""" % (
            nrOfVs, nrOfFs,
            statesRev[state], i
        )
    shape = SimpleShape(Vs, Fs, Es, colors = (cols, fColors))
    # Note that Orbitit's panel.setShape will ignore these anyway...
    if vRadius != 0:
        shape.setVertexProperties(radius = vRadius)
    if eRadius != 0:
        shape.setEdgeProperties(radius = eRadius)
    if name != '':
        shape.name = name
    # If the file defines edges (faces of length 2) then don't recreate any
    # edges, even if requested
    if recreateEdges and len(Es) == 0:
        shape.recreateEdges()
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
    def __init__(self, p0, p1 = None, v = None, d = 3, isSegment = False):
        """
        Define a line in a d dimensional space.

        Either specify two distinctive points p0 and p1 on the d dimensional
        line or specify a base point p0 and directional vector v. Points p0 and
        p1 should have accessable [0] .. [d-1] indices.
        """
        assert p1 == None or v == None, 'Specify either 2 points p0 and p1 or a base point p0 and a direction v!'
        self.dimension = d
        self.isSegment = isSegment
        if p1 != None:
            self.setPoints(p0, p1)
        elif v != None:
            self.setBaseDir(p0, v)

    def setPoints(self, p0, p1):
        d = [ p1[i] - p0[i] for i in range(self.dimension)]
        self.setBaseDir(p0, d)

    def setBaseDir(self, p, v):
        self.p = p
        self.v = v

    def factorInSegment(self, t, margin):
        return (
            t != None
            and
            (t >= 0 or eq(t, 0, margin))
            and
            (t <= 1 or eq(t, 1, margin))
        )

    def getPoint(self, t):
        """Returns the point on the line that equals to self.b + t*self.v (or [] when t == None)
        """
        if t != None:
            return [ self.p[i] + t * (self.v[i]) for i in range(self.dimension) ]
        else:
            return []

    def getFactorAt(self, c, i, margin = defaultFloatMargin):
        """
        Get the factor for one element constant. For an n-dimensional line it
        returns None if:
           1. the line lies in the (n-1) (hyper)plane x_i == c
           2. or the line never intersects the (n-1) (hyper)plane x_i == c.

        c: the constant
        i: index of element that should equal to c
        """
        if not eq(self.v[i], 0.0, margin):
            return (c - self.p[i]) / self.v[i]
        else:
            return None

    def vOnLine(self, v, margin = defaultFloatMargin):
        """
        Return True is V is on the line, False otherwise
        """
        t = self.getFactorAt(v[0], 0, margin)
        if t == None:
            t = self.getFactorAt(v[1], 1, margin)
        assert t != None
        return Veq(self.getPoint(t), v, margin, min(len(v), self.dimension))


    def getFactor(self, p, check = True, margin = defaultFloatMargin):
        """Assuming the point p lies on the line, the factor is returned.
        """
        for i in range(self.dimension):
            t =  self.getFactorAt(p[i], i, margin = margin)
            if not t == None:
                break
        assert t != None
        if check:
            c = self.getPoint(t)
            for i in range(1, self.dimension):
                if not eq(c[i], p[i], margin = margin):
                    print('The point is not on the line; yDiff =', (c[i]-p[i]))
                    raise PrecisionError('The point is not one the line;')
        if self.isSegment:
            if not (
                (t >= 0 or eq(t, 0, margin = margin))
                and
                (t <= 1 or eq(t, 1, margin = margin))
            ):
                print('The point is not one the line segment; t =', t)
                raise PrecisionError('The point is not one the line segment;')
        return t

class Line2D(Line):
    debug = False
    def __init__(self, p0, p1 = None, v = None, isSegment = False):
        """
        Define a line in a 2D plane.

        Either specify two distinctive points p0 and p1 on the line or specify
        a base point p0 and directional vector v. Points p0 and p1 should have
        accessable [0] and [1] indices.
        """
        Line.__init__(self, p0, p1, v, d = 2, isSegment = isSegment)

    def intersectLineGetFactor(self, l, margin = 10 * defaultFloatMargin):
        """Gets the factor for v for which the line l intersects this line

        i.e. the point of intersection is specified by self.p + restult * self.v
        If the lines are parallel, then None is returned.
        """
        nom = (l.v[0]*self.v[1]) - (l.v[1]*self.v[0])
        if not eq(nom, 0, margin):
            denom = l.v[0]*(l.p[1] - self.p[1]) + l.v[1]*(self.p[0] - l.p[0])
            return denom / nom
        else:
            return None

    def intersectLine(self, l):
        """returns the point of intersection with line l or None if the line is parallel.
        """
        return self.getPoint(self.intersectLineGetFactor(l))

    def intersectWithFacet(self, FacetVs, iFacet,
        z0 = 0.0,
        margin = defaultFloatMargin ,
        suppressWarn = False
    ):
        """
        Intersect the 2D line object in plane z = Z0 with a 3D facet and return
        the factors of the line where it intersects the edges.

        The 2D line object is lying in plane z = z0.
        The returned array is cleaned up such that intersections with vertices
        that just touch the a vertex without entering or exiting the facet are
        removed.
        FacetVs: the (possible 3 dimensional) vertices
        iFacet: the indices that form this facet. The indices refer to FacetVs
        z0    : defines the plane in which the 2D line is lying
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
        pOnLineAtEdges = []
        nrOfVs = len(iFacet)
        if self.debug:
            print('-------intersectWithFacet--------')
            print('facet indices:', iFacet)
        vertexIntersections = []
        for vertexNr in range(nrOfVs):
            v0 = FacetVs[iFacet[vertexNr]]
            v1 = FacetVs[iFacet[(vertexNr + 1) % nrOfVs]]
            v0 = geomtypes.Vec(v0)
            v1 = geomtypes.Vec(v1)
            if self.debug:
                print('==> intersect line with edge nr', vertexNr, '=', v0, '->', v1)
                print('(with this current line obect: {', self.p, ' + t*', self.v, ')')

            # PART 1.
            edgePV3D = Line3D(v0, v = v1-v0)
            t = edgePV3D.getFactorAt(z0, 2, margin = margin)
            s = None
            if t != None:
                tEq0 = eq(t, 0, margin)
                tEq1 = eq(t, 1, margin)
                if (t >= 0 or tEq0) and (t <= 1 or tEq1):
                    if self.debug:
                        print('edge intersects plane z =', z0,\
                            'in a point (t = %f)' % (t))
                    try:
                        s = self.getFactor(edgePV3D.getPoint(t),
                                                                margin = margin)
                    except PrecisionError:
                        s = None
                else:
                    if self.debug:
                        print('edge intersects plane z =', z0, 'but only if exteded (t =', t, ')')
            else:
                # Either the edge lies in the plane z = z0
                # or it is parallel with this plane
                liesInPlane = eq(v0[2], z0, margin)
                if liesInPlane:
                    if self.debug:
                        print('edge lies in plane z =', z0)
                    edgePV2D = Line2D(v0, v = v1-v0)
                    t = edgePV2D.intersectLineGetFactor(self, margin)
                    if t != None:
                        tEq0 = eq(t, 0, margin)
                        tEq1 = eq(t, 1, margin)
                        if (t >= 0 or tEq0) and (t <= 1 or tEq1):
                            s = self.intersectLineGetFactor(edgePV2D, margin)
                        else:
                            if self.debug:
                                print('edge intersects line but only if exteded (t =', t, ')')
                    else:
                        # fix getFactor so that just getFactor is needed.
                        if self.vOnLine(v0, margin):
                            tEq0 = True
                            tEq1 = False
                            s = self.getFactor(v0, margin = margin)
                            if self.debug:
                                print('edge is on the line')
                        else:
                            if self.debug:
                                print('edge is parallel to the line')
                else:
                    if self.debug:
                        print('edge parallel to plane z =', z0, '(no point of intersection)')
            if s != None:
                if self.debug:
                    print('FOUND s = ', s, ' with v =', self.getPoint(s))
                # ie. in this case tEq0 and tEq1 should be defined
                # only add vertex intersections once (otherwise you add the
                # intersection for edge_i and edge_i+1
                if not tEq1:
                    # each item is an array that holds
                    # 0. the vertex nr
                    # 1. the index of s in pOnLineAtEdges
                    if tEq0:
                        vertexIntersections.append([vertexNr, len(pOnLineAtEdges)])
                        if self.debug:
                            print('vertex intersection at v0')
                    pOnLineAtEdges.append(s)
                    if self.debug:
                        print('added s = ', s)
                else:
                    if self.debug:
                        print('vertex intersection at v1, ignored')

        if self.debug:
            print('line intersects edges (vertices) at s =', pOnLineAtEdges)
            print('vertex intersections:', vertexIntersections)
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
            if (vertexIndexDelta == 1 or vertexIndexDelta == nrOfVs - 1):
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
                    or
                    vertexIndexDelta >= nrOfVs - (
                        nrOfIntersectionsWithVertices - 1
                    )
                ):
                    allOnOneEdge = False
            if allOnOneEdge:
                # see remark above for nrOfIntersectionsWithVertices == 2
                allowOddNrOfIntersections = True
            else:
                # more than 2: complex cases.
                if not suppressWarn:
                        print('WARNING: intersections through more than 2',\
                                                'vertices (not on one edge)')
                        print('         vertexIntersections',\
                                                        vertexIntersections)
                        print('         pOnLineAtEdges', pOnLineAtEdges)
                        print('         will draw one long line, instead of'\
                                                                'segments')
                #assert False, 'ToDo'
                # if an assert is not wanted, choose pass.
                #allowOddNrOfIntersections = True
                pOnLineAtEdges.sort()
                pOnLineAtEdges = [pOnLineAtEdges[0], pOnLineAtEdges[-1]]
                if not suppressWarn:
                        print('         using pOnLineAtEdges', pOnLineAtEdges)
                pass
        pOnLineAtEdges.sort()

#        pOnLineAtEdges.sort()
#        if self.debug: print 'pOnLineAtEdges', pOnLineAtEdges, 'before clean up'
#        for s in range(1, len(pOnLineAtEdges)):
#            if eq(pOnLineAtEdges[s-1], pOnLineAtEdges[s], margin):
#                intersectionsWithVertex.append(s)
#                if self.debug:
#                    print 'intersection with vertex:', self.getPoint(s)
#        nrOfIntersectionsWithVertices = len(intersectionsWithVertex)
#        if self.debug: print pOnLineAtEdges
#        if nrOfIntersectionsWithVertices > 1:
#            # For this more work is needed, e.g. to distinguish a situation
#            # where this line intersects with 2 vertices only.  In that case it
#            # either just touches the vertices or it enters and exits the face
#            # through the vertices.
#            print 'facet indices:', iFacet
#            print 'facet vertices:'
#            for ind in iFacet: print FacetVs[ind], '%', ind
#            assert False, 'ToDo'
#            pass
#            # Walk through the intersections and keep track whether this is a
#            # transmission from 'outside' to 'inside' (the face). When a vertex
#            # intersections occurs, then check whether the point between this
#            # intersection and the next intersection lies 'inside' or 'outside'
#            # by drawing a new line from this point (not parallel to this line)
#        else:
#            if nrOfIntersectionsWithVertices == 1:
#                # Trivial, just keep nr of intersections even:
#                pInLoiIndex = intersectionsWithVertex[0]
#                if len(pOnLineAtEdges) % 2 == 0:
#                    del pOnLineAtEdges[pInLoiIndex-1: pInLoiIndex+1]
#                else:
#                    del pOnLineAtEdges[pInLoiIndex]
        if self.debug: print('pOnLineAtEdges', pOnLineAtEdges, 'after clean up')
        assert len(pOnLineAtEdges) % 2 == 0 or allowOddNrOfIntersections, "The nr of intersections should be even, are all edges unique and do they form one closed face?"
        if self.debug: print('=======intersectWithFacet========')
        return pOnLineAtEdges

class Line3D(Line):
    def __init__(self, p0, p1 = None, v = None, isSegment = False):
        """
        Define a line in 3D space.

        Either specify two distinctive points p0 and p1 on the line or specify
        a base point p0 and directional vector v. Points p0 and p1 should have
        a length of 3 and may be vec.
        """
        # make sure to have vec types internally
        p0 = geomtypes.Vec3(p0)
        if p1 == None:
            assert v != None
            v = geomtypes.Vec3(v)
            Line.__init__(self, p0, v = v, d = 3, isSegment = isSegment)
        else:
            assert v == None
            p1 = geomtypes.Vec3(p1)
            Line.__init__(self, p0, p1, d = 3, isSegment = isSegment)

    # redefine to get vec3 types:
    def setPoints(self, p0, p1):
        self.setBaseDir(p0, p1-p0)

    def getPoint(self, t):
        if t != None:
            return self.p + t * self.v
        else:
            return []

    def squareDistance2Point(self, P):
        # p81 of E.Lengyel
        q = vec(P)
        hyp = q - self.p
        prjQ = hyp*self.v
        return (hyp*hyp) - ((prjQ*prjQ) / (self.v*self.v))

    def Discriminant2Line(self, L):
        # p82 of E.Lengyel
        dot = (self.v*L.v)
        return (self.v*self.v)*(L.v*L.v) - dot*dot

    def isParallel2Line(self, L):
        # p82 of E.Lengyel
        return self.Discriminant2Line(L) == 0

    def intersectWithLine(self, L, check = True, margin = defaultFloatMargin):
        D = self.Discriminant2Line(L)
        if D == 0: return None
        dx = (L.p - self.p) * self.v
        dy = (self.p - L.p) * L.v
        vpvq = self.v * L.v
        s = ((L.v * L.v) * dx +  vpvq * dy) / D
        if self.isSegment and not self.factorInSegment(s, margin):
            result = None
        else:
            result = self.getPoint(s)
            if check:
                t = (vpvq * dx + (self.v * self.v) * dy) / D
                if L.isSegment and not L.factorInSegment(t, margin):
                    result = None
                else:
                    checkWith = L.getPoint(t)
                    if (not Veq(result, checkWith, margin = margin)):
                        result = None
                    else:
                        # for a better precision:
                        result = (result + checkWith) / 2
        return result

    def toStr(self, precision = 2):
        formatStr = "(x, y, z) = (%%0.%df, %%0.%df, %%0.%df) + t * (%%0.%df, %%0.%df, %%0.%df)" % (precision, precision, precision, precision, precision, precision)
        return formatStr % (self.p[0], self.p[1], self.p[2], self.v[0], self.v[1], self.v[2])

class Triangle:
    def __init__(self, v0, v1, v2):
        self.v = [
                vec(v0[0], v0[1], v0[2]),
                vec(v1[0], v1[1], v1[2]),
                vec(v2[0], v2[1], v2[2])
            ]
        self.N = None

    def normal(self, normalise = False):
        if self.N == None:
            self.N = (self.v[1] - self.v[0]).cross(self.v[2] - self.v[0])
            if normalise:
                try: self.N = self.N.normalize()
                except ZeroDivisionError: pass
            return self.N
        else:
            return self.N

class Plane:
    """Create a plane from 3 points in the plane.

    The points should be unique.
    The plane class will contain the fields 'N' expressing the normalised norm
    and a 'D' such that for a point P in the plane 'D' = -N.P, i.e. Nx x + Ny y
    + Nz z + D = 0 is the equation of the plane.
    """
    def __init__(self, P0, P1, P2):
        assert(not P0 == P1), '\n  P0 = %s,\n  P1 = %s' % (str(P0), str(P1))
        assert(not P0 == P2), '\n  P0 = %s,\n  P2 = %s' % (str(P0), str(P2))
        assert(not P1 == P2), '\n  P1 = %s,\n  P2 = %s' % (str(P1), str(P2))
        self.N = self.norm(P0, P1, P2)
        self.D = -self.N * geomtypes.Vec3(P0)

    def norm(self, P0, P1, P2):
        """calculate the norm for the plane
        """
        v1 = geomtypes.Vec3(P0) - geomtypes.Vec3(P1)
        v2 = geomtypes.Vec3(P0) - geomtypes.Vec3(P2)
        cross = v1.cross(v2)
        if eq(cross.norm(), 0):
            raise ValueError("Points are on one line")
        return v1.cross(v2).normalize()

    def intersectWithPlane(self, plane):
        """Calculates the intersections of 2 planes.

        If the planes are parallel None is returned (even if the planes define
        the same plane) otherwise a line is returned.
        """
        if plane == None:
            return None
        N0 = self.N
        N1 = plane.N
        if N0 == N1 or N0 == -N1:
            return None
        V = N0.cross(N1)
        #V = V.normalise()
        # for toPsPiecesStr self.N == [0, 0, 1]; hanlde more efficiently.
        if N0 == geomtypes.Vec([0, 0, 1]):
            # simplified situation from below:
            z = -self.D
            M = geomtypes.Mat([geomtypes.Vec(N1[0:2]), geomtypes.Vec(V[0:2])])
            #print 'M', M
            #print 'V', geomtypes.Vec([-plane.D - N1[2]*z, -V[2]*z])
            Q = M.solve(geomtypes.Vec([-plane.D - N1[2]*z, -V[2]*z]))
            Q = geomtypes.Vec([Q[0], Q[1], z])
        else:
            # See bottom of page 86 of Maths for 3D Game Programming.
            M = geomtypes.Mat([N0, N1, V])
            #print 'M', M
            #print 'V', geomtypes.Vec([-self.D, -plane.D, 0])
            Q = M.solve(geomtypes.Vec([-self.D, -plane.D, 0]))
        return Line3D(Q, v = V)

    def toStr(self, precision = 2):
        formatStr = "%%0.%df*x + %%0.%df*y + %%0.%df*z + %%0.%df = 0)" % (precision, precision, precision, precision)
        return formatStr % (self.N[0], self.N[1], self.N[2], self.D)

def facePlane(Vs, face):
    """
    Define a Plane object from a face

    Vs: the 3D vertex coordinates
    face: the indices in Vs that form the face.
    Returns None if the vertices do not define a plane.
    """
    assert len(face) > 2, 'a face should at least be a triangle'
    #print len(Vs)
    #print face
    plane = None
    planeFound = False
    fi_0 = 1
    fi_1 = 2
    while not planeFound:
        try:
            # print 0, fi_0, fi_1
            # print Vs[face[0]], Vs[face[fi_0]], Vs[face[fi_1]]
            plane = Plane(
                    Vs[face[0]],
                    Vs[face[fi_0]],
                    Vs[face[fi_1]]
                )
            planeFound = True
        except ValueError or AssertionError:
            fi_1 += 1
            if fi_1 >= len(face):
                fi_0 += 1
                fi_1 = fi_0 + 1
                if fi_1 >= len(face):
                    print("Ignoring degenerate face (line or point?)")
                    break
    return plane

TRI_CW = 1 # clockwise triangle vertices to get outer normal
TRI_CCW = 2 # counter-clockwise triangle vertices to get outer normal
TRI_OUT = 3  # the normal pointing away from the origin is the normal
TRI_IN = 4 # the normal pointing towards from the origin is the normal


class SimpleShape(base.Orbitit):
    normal_direction = TRI_OUT

    """
    This class decribes a simple 3D object consisting of faces and edges.
    """
    def __init__(self,
        Vs, Fs, Es = [], Ns = [],
        colors = ([], []), name = "SimpleShape",
        orientation = None
    ):
        """
        Vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        Fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        Es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        Ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by glDraw
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each face with
                   index 'i' in Fs which colour index from the parameter color
                   is used for this face.  If empty then colors[0][0] shall be
                   used for each face.
        name: A string expressing the name. This name is used e.g. when
            exporting to other formats, like PS.
        orientation: orientation of the base shape. This is an isometry operation.
        """
        self.dimension = 3
        self.fNs = []
        self.generateNormals = True
        self.name = name
        self.glInitialised = False
        self.gl = Fields()
        self.gl.sphere = None
        self.gl.cyl = None
        self.gl.alwaysSetVertices = False # set to true if a scene contains more than 1 shape
        if colors[0] == []:
            colors = ([rgb.gray95[:]], [])
        self.scalingFactor = 1.0
        self.setVertexProperties(Vs = Vs, Ns = Ns, radius = -1., color = [1. , 1. , .8 ])
        self.setEdgeProperties(
            Es = Es, radius = -1., color = [0.1, 0.1, 0.1], drawEdges = True
        )
        self.setFaceProperties(
            Fs = Fs, colors = colors, drawFaces = True
        )
        self.defaultColor = rgb.yellow
        if orientation:
            self.orientation = orientation
            if not orientation.is_rot():
                self.normal_direction = TRI_IN
        else:
            self.orientation = geomtypes.E

    def __repr__(self):
        #s = indent.Str('%s(\n' % base.find_module_class_name(self.__class__, __name__))
        s = indent.Str('SimpleShape(\n')
        s = s.add_incr_line('Vs=[')
        s.incr()
        try:
            s = s.glue_line(',\n'.join(
                indent.Str(repr(v)).reindent(s.indent) for v in self.Vs)
            )
        except AttributeError:
            print('ERROR: Are you sure the vertices are all of type geomtypes.Vec3?')
            raise
        s = s.add_decr_line('],')
        s = s.add_line('Fs=[')
        s.incr()
        s = s.glue_line(',\n'.join(
            indent.Str(repr(f)).reindent(s.indent) for f in self.Fs)
        )
        s = s.add_decr_line('],')
        s = s.add_line('Es=%s,' % repr(self.Es))
        s = s.add_line('colors=%s,' % repr(self.colorData))
        s = s.add_line('name="%s"' % self.name)
        s = s.add_decr_line(')')
        if __name__ != '__main__':
            s = s.insert('%s.' % __name__)
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object.

        Only essential parts are saved. E.g. orientation isn't essential here.
        """
        return {
            'class': base.class_to_json[self.__class__],
            'data': {
                'name': self.name,
                'vs': self.Vs,
                'fs': self.Fs,
                'cols': self.colorData[0],
                'face_cols': self.colorData[1],
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        return cls(data["vs"], data["fs"], colors=(data["cols"], data["face_cols"]), name=data["name"])

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
        v_props = self.getVertexProperties()
        f_props = self.getFaceProperties()
        fs = f_props['Fs']
        org_cols = f_props['colors']
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
        shape.setVertexProperties(v_props)
        f_props['Fs'] = new_fs
        f_props['colors'] = new_cols
        shape.setFaceProperties(f_props)
        return shape


    def cleanShape(self, precision):
        """Return a new shape for which vertices are merged and degenerated faces are deleted.

        The shape will not have any edges.
        """
        vProps = self.getVertexProperties()
        fProps = self.getFaceProperties()
        cpVs = copy.deepcopy(vProps['Vs'])
        cpFs = copy.deepcopy(fProps['Fs'])
        glue.mergeVs(cpVs, cpFs, precision)
        # this may result on less faces, which breaks the colours!
        # TODO either update the colors immediately or return an array with
        # deleted face indices.
        glue.cleanUpVsFs(cpVs, cpFs)
        vProps['Vs'] = cpVs
        fProps['Fs'] = cpFs
        shape = SimpleShape([], [], [])
        shape.setVertexProperties(vProps)
        shape.setFaceProperties(fProps)
        return shape

    def setVs(self, Vs):
        self.setVertexProperties(Vs = Vs)

    def setVertexProperties(self, dictPar = None, **kwargs):
        """
        Set the vertices and how/whether vertices are drawn in OpenGL.

        Accepted are the optional (keyword) parameters:
        - Vs,
        - radius,
        - color.
        - Ns.
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equal to None) they are not changed.
        See getVertexProperties for the explanation of the keywords.
        The output of getVertexProperties can be used as the dictPar parameter.
        This can be used to copy settings from one shape to another.
        If dictPar is used and kwargs, then only the dictPar will be used.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Vs' in dict and dict['Vs'] != None:
                self.Vs = dict['Vs']
                self.VsRange = range(len(dict['Vs']))
                self.gl.updateVs = True
                self.fNsUp2date = False
            if 'Ns' in dict and dict['Ns'] != None:
                self.Ns = dict['Ns']
            if 'radius' in dict and dict['radius'] != None:
                self.gl.vRadius     = dict['radius']
                self.gl.addSphereVs = dict['radius'] > 0.0
                if self.gl.addSphereVs:
                    if self.gl.sphere != None: del self.gl.sphere
                    self.gl.sphere = Scenes3D.VSphere(radius = dict['radius'])
            if 'color' in dict and dict['color'] != None:
                self.gl.vCol = dict['color']

    def getVertexProperties(self):
        """
        Return the current vertex properties as can be set by setVertexProperties.

        Returned is a dictionary with the keywords Vs, radius, color.
        Vs: an array of vertices.
        radius: If > 0.0 draw vertices as spheres with the specified colour. If
                no spheres are required (for preformance reasons) set the radius
                to a value <= 0.0.
        color: optianl array with 3 rgb values between 0 and 1.
        Ns: an array of normals (per vertex) This value might be None if the
            value is not set. If the value is set it is used by glDraw
        """
        return {
            'Vs': self.Vs,
            'radius': self.gl.vRadius,
            'color': self.gl.vCol,
            'Ns': self.Ns
        }

    def gl_alwaysSetVertices(self, do):
        self.gl.alwaysSetVertices = do

    def setEdgeProperties(self, dictPar = None, **kwargs):
        """
        Specify the edges and set how they are drawn in OpenGL.

        Accepted are the optional (keyword) parameters:
          - Es,
          - radius,
          - color,
          - drawEdges.
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equel to None) they are not changed.
        See getEdgeProperties for the explanation of the keywords.
        The output of getEdgeProperties can be used as the dictPar parameter.
        This can be used drawFacesto copy settings from one shape to another.
        If dictPar is used and kwargs, then only the dictPar will be used.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Es' in dict and dict['Es'] != None:
                self.Es = dict['Es']
                self.EsRange = range(0, len(self.Es), 2)
            if 'radius' in dict and dict['radius'] != None:
                self.gl.eRadius       = dict['radius']
                self.gl.useCylinderEs = dict['radius'] > 0.0
                if self.gl.useCylinderEs:
                    if self.gl.cyl != None: del self.gl.cyl
                    self.gl.cyl = Scenes3D.P2PCylinder(radius = dict['radius'])
            if 'color' in dict and dict['color'] != None:
                self.gl.eCol = dict['color']
            if 'drawEdges' in dict and dict['drawEdges'] != None:
                self.gl.drawEdges = dict['drawEdges']
            #print 'drawEdge:', self.gl.drawEdges, 'radius:', radius#, 'Es', self.Es

    def getEdgeProperties(self):
        """
        Return the current edge properties as can be set by setEdgeProperties.

        Returned is a dictionary with the keywords Es, radius, color, drawEdges
        Es: a qD array of edges, where i and j in edge [ .., i, j,.. ] are
            indices in Vs.
        radius: If > 0.0 draw vertices as cylinders with the specified colour.
                If no cylinders are required (for preformance reasons) set the
                radius to a value <= 0.0 and the edges will be drawn as lines,
                using glPolygonOffset.
        color: array with 3 rgb values between 0 and 1.
        drawEdges: settings that expresses whether the edges should be drawn at
                   all.
        """
        return {'Es': self.Es,
                'radius': self.gl.eRadius,
                'color': self.gl.eCol,
                'drawEdges': self.gl.drawEdges
            }

    def recreateEdges(self):
        """
        Recreates the edges in the 3D object by using an adges for every side of
        a face, i.e. all faces will be surrounded by edges.

        Edges will be filtered so that shared edges between faces,
        i.e. edges that have the same vertex index, only appear once.
        The creation of edges is not optimised and can take a long time.
        """
        Es2D = []
        Es = []
        def addEdge(i, j):
            if   i < j: edge = [i, j]
            elif i > j: edge = [j, i]
            else: return
            if not edge in Es2D:
                Es2D.append(edge)
                Es.extend(edge)
        for face in self.Fs:
            lastIndex = len(face) - 1
            for i in range(lastIndex):
                addEdge(face[i], face[i+1])
            # handle the edge from the last vertex to the first vertex separately
            # (instead of using % for every index)
            addEdge(face[lastIndex], face[0])
        self.setEdgeProperties(Es = Es)

    def setFs(self, Fs):
        self.setFaceProperties(Fs = Fs)

    def setFaceProperties(self, dictPar = None, **kwargs):
        """
        Define the properties of the faces.

        Accepted are the optional (keyword) parameters:
          - Fs,
          - colors,
          - drawFaces.
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equal to None) they are not changed.
        See getFaceProperties for the explanation of the keywords.
        The output of getFaceProperties can be used as the dictPar parameter.
        This can be used to copy settings from one shape to another.
        If dictPar is used and kwargs, then only the dictPar will be used.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Fs' in dict and dict['Fs'] != None:
                self.__setFs(dict['Fs'])
            if 'colors' in dict and dict['colors'] != None:
                self.setFaceColors(dict['colors'])
            self.divideColorWrapper()
            if 'drawFaces' in dict and dict['drawFaces'] != None:
                self.setEnableDrawFaces(dict['drawFaces'])

    def getFaceProperties(self):
        """
        Return the current face properties as can be set by setFaceProperties.

        Returned is a dictionary with the keywords Fs, colors, and drawFaces.
        Fs: Optional array of faces, that do not need to be triangular. It is a
            hierarchical array, ie it consists of sub-array, where each
            sub-array describes one face. Each n-sided face is desribed by n
            indices. Empty on default. Using triangular faces only gives a
            better performance.
            If Fs == None, then the previous specified value will be used.
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each face with
                   index 'i' in Fs which colour index from the parameter color
                   is used for this face. If empty then colors[0][0] shall be
                   used for each face.
                   It should have the same length as Fs (or the current faces if
                   Fs not specified) otherwise the parameter is ignored and the
                   face colors are set by some default algorithm.
        drawFaces: settings that expresses whether the faces should be drawn.
        """
        return {'Fs': self.Fs,
                'colors': self.colorData,
                'drawFaces': self.gl.drawFaces
            }

    def triangulate(self, Fs):
        ts = []
        for f in Fs:
            triF = []
            #print 'f', f
            for i in range(1, len(f)-1):
                # i+1 before i, to keep clock-wise direction
                triF.extend([f[0], f[i+1], f[i]])
                #print 'triF.extend: [', f[0], ',', f[i+1], ',', f[i], ']'
            ts.append(triF)
        return ts

    def __setFs(self, Fs):
        """
        Define the shape faces

        Fs: see getFaceProperties.
        """
        for f in Fs:
            assert (len(f) > 2), "A face should have at least 3 vertices"
        self.Fs = Fs
        self.TriangulatedFs = self.triangulate(Fs)
        #print 'Fs', Fs
        self.FsLen = len(self.Fs)
        self.FsRange = range(self.FsLen)
        self.fNsUp2date = False
        # if you autogenerate the vertex normal, using the faces, you need to
        # regenerate by setting self.gl.updateVs
        self.gl.updateVs = self.generateNormals

    def setFaceColors(self, colors):
        """
        Define the colours of the faces.

        colors: see getFaceProperties.
        """
        if colors[0] != None:
            colorDefs  = colors[0]
        else:
            colorDefs  = self.colorData[0]
        if colors[1] != None:
            fColors = colors[1]
        else:
            fColors = self.colorData[1]
        self.colorData = (colorDefs, fColors)
        self.nrOfColors = len(colorDefs)
        self.colRange = range(self.nrOfColors)
        assert(self.nrOfColors > 0), 'Empty colorDefs: %s' % colorDefs

    def getFaceColors(self):
        """
        Get the colours of the faces.

        Same as getFaceProperties()['colors'] but provided since setFaceColors
        exists.
        """
        return self.colorData

    def setEnableDrawFaces(self, draw = True):
        """
        Set whether the faces need to be drawn in glDraw (or not).

        draw: optional argument that is True by default. Set to False to
              disable drawing of the faces.
        """
        self.gl.drawFaces = draw

    def generate_face_normal(self, f, normalise):
        l = len(f)
        assert l > 2, 'An face should at least have 2 vertices'
        if l < 3:
            assert False, 'Normal for digons not implemented'
            # TODO: what to do here?
        normal = Triangle(
            self.Vs[f[0]], self.Vs[f[1]], self.Vs[f[2]]
        ).normal(normalise)
        if self.normal_direction == TRI_OUT or self.normal_direction == TRI_IN:
            v0 = geomtypes.Vec3(self.Vs[f[0]])
            outwards = v0.norm() < (v0 + normal).norm()
            if ((outwards and self.normal_direction == TRI_IN) or
                (not outwards and self.normal_direction == TRI_OUT)
            ):
                normal = -normal
        return normal

    def createFaceNormals(self, normalise):
        # TODO use smarter sol than self.fNsNormalised != normalise:
        # if already normalised, you never need to recalc
        # if not yet normalised, but required, just normalise.
        if not self.fNsUp2date or self.fNsNormalised != normalise:
            self.fNs = [self.generate_face_normal(f, normalise) for f in self.Fs]
            self.fNsUp2date = True
            self.fNsNormalised = normalise

    def createVertexNormals(self, normalise, Vs = None):
        if Vs == None: Vs = self.Vs
        self.createFaceNormals(normalise)
        # only use a vertex once, since the normal can be different
        self.nVs = []
        self.vNs = []
        for face, normal in zip(self.Fs, self.fNs):
            self.vNs.extend([normal for vi in face])
            self.nVs.extend([[Vs[vi][0], Vs[vi][1], Vs[vi][2]] for vi in face])
        self.createVertexNormals_vi = -1
        def inc():
            self.createVertexNormals_vi += 1
            return self.createVertexNormals_vi
        self.nFs = [[inc() for i in face] for face in self.Fs]
        self.TriangulatedFs = self.triangulate(self.nFs)
        # Now for the edge vertices. Note that edge vertices aren't necessarily
        # part of the face vertices.
        edgeIndexOffset = len(self.nVs)
        self.nVs.extend(Vs)
        if normalise:
            for v in Vs:
                self.vNs.append(v.normalize())
        else:
            for v in Vs:
                self.vNs.append(v)
        self.nEs = [oldVi + edgeIndexOffset for oldVi in self.Es]

    def createEdgeLengths(self, precision = 12):
        e2l = {}
        l2e = {}
        for ei in self.EsRange:
            vi0 = self.Es[ei]
            vi1 = self.Es[ei+1]
            if vi0 < vi1: t = (vi0, vi1)
            else:         t = (vi1, vi0)
            l = (geomtypes.Vec3(self.Vs[vi1]) - geomtypes.Vec3(self.Vs[vi0])
                ).norm()
            e2l[t] = l
            l = round(l, precision)
            try: l2e[l].append(t)
            except KeyError: l2e[l] = [t]
        self.e2l = e2l
        self.l2e = l2e
        return l2e

    def createDihedralAngles(self, precision = 12):
        self.createFaceNormals(normalise = False)
        e2d = {}
        d2e = {}
        lFs = len(self.Fs)
        def addDihedralAngle(fi, cFace, cfi, vi, i, viRef, e2d, d2e):
            # fi: face index of face under investigation
            # cFace: the face we are checking against (a list of vertex indices)
            # cfi: index of face we are checking against
            # vi: vertex index we are looking at (which is part of the face
            #     under investigation and of cFace)
            # i: index of vi in cFace.
            # viRef: the vertex that will be checked for in cFace.
            # e2d: dictionary mapping edges on dihedral angles, using index
            #      tuples as keys
            # d2e: dictionary mapping dihedral angles on edges, using angles as
            #      tuples
            _i = i - 1
            if _i < 0: _i = len(cFace) - 1
            i_ = i + 1
            if i_ >= len(cFace): i_ = 0
            # if the vertex vi - viRef is part of cFace
            if (cFace[_i] == viRef or cFace[i_] == viRef):
                # add the angle to d array.
                if vi < viRef: t = (vi, viRef)
                else:          t = (viRef, vi)
                angle = math.pi - self.fNs[fi].angle(self.fNs[cfi])
                angle = round(angle, precision)
                try: e2d[t].append(angle)
                except KeyError: e2d[t] = [angle]
                try: d2e[angle].append(t)
                except KeyError: d2e[angle] = [t]
        for face, fi in zip(self.Fs, self.FsRange):
            f_ = face[:]
            f_.append(face[0])
            l = len(f_)
            for fii in range(1, l, 2):
                vi = f_[fii]
                vip = f_[fii-1] # previous x
                #print fii, f_, '@', vi
                if fii >= l-1:
                    vin = -1 # no next
                else:
                    vin = f_[fii+1] # next
                for nfi in range(fi+1, lFs):
                    nFace = self.Fs[nfi]
                    try: i = nFace.index(vi)
                    except ValueError: i = -1
                    if i >= 0:
                        addDihedralAngle(fi, nFace, nfi, vi, i, vip, e2d, d2e)
                        addDihedralAngle(fi, nFace, nfi, vi, i, vin, e2d, d2e)
        self.e2d = e2d
        self.d2e = d2e
        return d2e

    def divideColorWrapper(self):
        """
        Divide the specified colours over the faces.

        This function wraps the divideColor function and handles the trivial
        cases for which there is only one colour of for which there are more
        colours than faces. These trivial cases do not need to be implemented by
        every descendent.
        """
        if (len(self.colorData[1]) != self.FsLen):
            if self.nrOfColors == 1:
                self.colorData = (
                        self.colorData[0],
                        [0 for i in self.FsRange]
                    )
            elif self.nrOfColors < self.FsLen:
                self.divideColor()
            else:
                self.colorData = (
                        self.colorData[0],
                        list(range(self.FsLen))
                    )
            assert(len(self.colorData[1]) == self.FsLen)
        # generate an array with Equal coloured faces:
        self.EqColFs = [[] for col in range(self.nrOfColors)]
        for i in self.FsRange:
            self.EqColFs[self.colorData[1][i]].append(i)

    def divideColor(self):
        """
        Divide the specified colours over the isometries.

        This function should actually be implemented by a descendent, so that
        the colours can be divided according to the symmetry. This function
        just repeats the colours until the length is long enough.
        The amount of colours should be less than the nr of isomentries.
        """
        div = self.FsLen // self.nrOfColors
        mod = self.FsLen % self.nrOfColors
        fColors = []
        colorIRange = list(range(self.nrOfColors))
        for i in range(div):
            fColors.extend(colorIRange)
        fColors.extend(list(range(mod)))
        self.colorData = (self.colorData[0], fColors)

    def scale(self, scale):
        self.scalingFactor = scale
        self.gl.updateVs = True

    def calculateFacesG(self):
        self.fGs = [
            reduce(lambda t, i: t + self.Vs[i], f, vec(0, 0, 0)) / len(f)
            for f in self.Fs
        ]

    def calculateSphereRadii(self, precision=12):
        """Calculate the radii for the circumscribed, inscribed and mid sphere(s)
        """
        # calculate the circumscribed spheres:
        self.spheresRadii = Fields()
        self.spheresRadii.precision = precision
        s = {}
        for v in self.Vs:
            r = round(v.norm(), precision)
            try: cnt = s[r]
            except KeyError: cnt = 0
            s[r] = cnt + 1
        self.spheresRadii.circumscribed = s
        s = {}
        for i in self.EsRange:
            v = (self.Vs[self.Es[i]] +  self.Vs[self.Es[i+1]]) / 2
            r = round(v.norm(), precision)
            try: cnt = s[r]
            except KeyError: cnt = 0
            s[r] = cnt + 1
        self.spheresRadii.mid = s
        s = {}
        try: G = self.fGs
        except AttributeError:
            self.calculateFacesG()
        for g in self.fGs:
            r = round(g.norm(), precision)
            try: cnt = s[r]
            except KeyError: cnt = 0
            s[r] = cnt + 1
        self.spheresRadii.inscribed = s

    def glInit(self):
        """
        Initialise OpenGL for specific shapes

        Enables a derivative to use some specific OpenGL settings needed for
        this shape. This function is called in glDraw for the first time glDraw
        is called.
        """
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY);
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glDisable(GL.GL_CULL_FACE)

        self.glInitialised = True

    def glDraw(self):
        """
        Draw the base element according to the definition of the Vs, Es, Fs and
        colour settings.

        Use self.setVertexProperties(), and setEdgeProperties and
        setFaceProperties to specify how and whether to draw the vertices, edges
        and faces respectively.
        """
        if self.Vs == []: return
        Es = self.Es
        if not self.glInitialised:
            self.glInit()
        # have this one here and not in glDraw, so that a client can call this
        # function as well (without having to think about this)

        # Check if unity matrix?
        GL.glPushMatrix()
        GL.glMultMatrixd(self.orientation.glMatrix())
        if self.gl.updateVs:
            # calculate the gravitational centre. Only calculate the vertices
            # that are used:
            if eq(self.scalingFactor, 1.0):
                Vs = self.Vs
            else:
                nrUsed = glue.getVUsageIn1D(self.Vs, self.Es)
                nrUsed = glue.getVUsageIn2D(self.Vs, self.Fs, nrUsed)
                g = vec(0, 0, 0)
                sum = 0
                for vIndex in self.VsRange:
                    g = g + nrUsed[vIndex] * vec(self.Vs[vIndex])
                    sum = sum + nrUsed[vIndex]
                if sum != 0:
                    g = g / sum
                #print self.name, 'g:', g
                Vs = [self.scalingFactor * (vec(v) - g) + g for v in self.Vs]

            # At least on Ubuntu 8.04 conversion is not needed
            # On windows and Ubuntu 9.10 the Vs cannot be an array of vec3...
            if not self.generateNormals:
                try:
                    GL.glVertexPointerf(Vs)
                    Ns = self.Ns
                except TypeError:
                    Vs = [ [v[0], v[1], v[2]] for v in Vs ]
                    print("glDraw: converting Vs(Ns); vec3 type not accepted")
                    GL.glVertexPointerf(Vs)
                    Ns = [ [v[0], v[1], v[2]] for v in self.Ns ]
                if Ns != []:
                    assert len(Ns) == len(Vs), 'the normal vector array Ns should have as many normals as  vertices.'
                    GL.glNormalPointerf(Ns)
                    self.NsSaved = Ns
                else:
                    GL.glNormalPointerf(Vs)
                    self.NsSaved = Vs
            elif self.Ns != [] and len(self.Ns) == len(Vs):
                try:
                    GL.glVertexPointerf(Vs)
                    Ns = self.Ns
                except TypeError:
                    Vs = [ [v[0], v[1], v[2]] for v in Vs ]
                    print("glDraw: converting Vs(Ns); vec3 type not accepted")
                    GL.glVertexPointerf(Vs)
                    Ns = [ [n[0], n[1], n[2]] for n in self.Ns ]
                GL.glNormalPointerf(Ns)
                self.NsSaved = Ns
            else:
                self.createVertexNormals(True, Vs)
                if self.nVs != []:
                    GL.glVertexPointerf(self.nVs)
                GL.glNormalPointerf(self.vNs)
                self.NsSaved = self.vNs
                Vs = self.nVs
            self.gl.updateVs = False
            self.VsSaved = Vs
        else:
            if self.gl.alwaysSetVertices:
                GL.glVertexPointerf(self.VsSaved)
                GL.glNormalPointerf(self.NsSaved)
        # VERTICES
        if self.gl.addSphereVs:
            GL.glColor(self.gl.vCol[0], self.gl.vCol[1], self.gl.vCol[2])
            for i in self.VsRange:
                self.gl.sphere.draw(self.Vs[i])
        # EDGES
        if self.gl.drawEdges:
            if self.generateNormals and (
                self.Ns == [] or len(self.Ns) != len(self.Vs)):
                Es = self.nEs
                Vs = self.nVs
            else:
                Es = self.Es
                Vs = self.Vs
            GL.glColor(self.gl.eCol[0], self.gl.eCol[1], self.gl.eCol[2])
            if self.gl.useCylinderEs:
                # draw edges as cylinders
                #for i in range(0, len(self.Es), 2):
                for i in self.EsRange:
                    self.gl.cyl.draw(
                            v0 = Vs[Es[i]],
                            v1 = Vs[Es[i+1]]
                        )
            else:
                # draw edges as lines
                GL.glPolygonOffset(1.0, 3.)
                GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
                GL.glDrawElementsui(GL.GL_LINES, Es)
                GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)

        # FACES
        if self.gl.drawFaces:
            for colIndex in self.colRange:
                c = self.colorData[0][colIndex]
                if len(c) == 3:
                    GL.glColor(c[0], c[1], c[2])
                else:
                    GL.glColor(c[0], c[1], c[2], c[3])
                for faceIndex in self.EqColFs[colIndex]:
                    triangles = self.TriangulatedFs[faceIndex]
                    # Note triangles is a flat (ie 1D) array
                    if len(triangles) == 3:
                        GL.glDrawElementsui(GL.GL_TRIANGLES, triangles)
                    else:
                        # TODO: This part belongs to a GLinit:
                        GL.glClearStencil(0)
                        stencilBits = GL.glGetIntegerv(GL.GL_STENCIL_BITS)
                        assert stencilBits > 0, 'Only triangle faces are supported, since there is no stencil bit'
                        # << TODO: end part that belongs to a GLinit
                        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
                        # use stecil buffer to triangulate.
                        GL.glColorMask(GL.GL_FALSE, GL.GL_FALSE,
                                       GL.GL_FALSE, GL.GL_FALSE)
                        GL.glDepthMask(GL.GL_FALSE)
                        #glDepthFunc(GL.GL_ALWAYS)
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
                        #glDepthFunc(GL.GL_LESS)
                        if len(c) == 3:
                            GL.glDepthMask(GL.GL_TRUE)
                        GL.glColorMask(GL.GL_TRUE, GL.GL_TRUE,
                                       GL.GL_TRUE, GL.GL_TRUE)
                        # Draw only where stencil equals 1 (masked to 1)
                        # GL_INVERT was used, i.e. in case of e.g. 8 bits the value is
                        # either 0 or 0xff, but only the last bit is checked.
                        GL.glStencilFunc(GL.GL_EQUAL, 1, 1)
                        # make stencil read only:
                        GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)
                        # Now, write according to stencil
                        GL.glDrawElementsui(GL.GL_TRIANGLES, triangles)
                        if len(c) > 3:
                            GL.glDepthMask(GL.GL_TRUE)
                        # ready, disable stencil
                        GL.glDisable(GL.GL_STENCIL_TEST)
        GL.glPopMatrix()

    def toX3dNode(self, id = 'SISH', precision = 5, edgeRadius = 0):
        """
        Converts this SimpleShape to a X3dNode class and returns the result.

        id: A string that will be used to refer to this shape in X3D.
        precision: The precision that will be used for the coordinates of the
                   vertices when printing the result to an X3D or VRML formatted
                   string.
        edgeRadius: Optinal radius of the edges to be used when printing the
                    result to an X3D or VRML formatted string. If 0.0 then the
                    edges will be drawn as lines, otherwise cylinders will be
                    used (the latter will lead to a much heavier file, that will
                    be rendered much slower).
        """
        vName = '%sVs' % id
        sName = '%sTransform' % id
        shapes = [
                X3D.Node('Shape',
                    appearance = X3D.Node('Appearance',
                        material = X3D.Node('Material',
                            diffuseColor = X3D.FloatVec([1, 1, 1], 0)
                        )
                    ),
                    geometry = X3D.Node('IndexedFaceSet',
                        color = X3D.Node(
                                'Color',
                                color = [ X3D.FloatVec(col, precision)
                                        for col in self.colorData[0]
                                    ]
                            ),
                        coord = X3D.Node(
                                'Coordinate',
                                DEF = vName,
                                point = [ X3D.FloatVec(v, precision)
                                        for v in self.Vs
                                    ]
                            ),
                        coordIndex = [ X3D.Index(i) for i in self.Fs],
                        colorIndex = self.colorData[1],
                        normalPerVertex = False,
                        colorPerVertex  = False,
                        ccw             = False,
                        solid           = False,
                        creaseAngle     = 0.5
                    )
                )
            ]
        if not (self.Es == []):
            if edgeRadius <= 0:
                Es = []
                for i in range(0, len(self.Es), 2):
                    Es.append([self.Es[i], self.Es[i+1]])
                shapes.append(X3D.Node('Shape',
                    appearance = X3D.Node('Appearance',
                        material = X3D.Node('Material',
                            diffuseColor = X3D.FloatVec([0, 0, 0], 1)
                        )
                    ),
                    geometry = X3D.Node('IndexedLineSet',
                        coord = X3D.Node('Coordinate', USE = vName),
                        coordIndex = [ X3D.Index(i) for i in Es]
                    )
                ))
            else:
                Es2D = []
                i = 0
                # TODO cylinderEdgesToX3d shoudl accept a flat array...
                while i < len(self.Es):
                    Es2D.append([self.Es[i], self.Es[i+1]])
                    i += 2
                shapes.append(glue.cylinderEdgesToX3d(Es2D, self.Vs, edgeRadius))
        return X3D.Node('Transform', DEF = sName, children = shapes)

    def toX3dDoc(self, id = 'SISH', precision = 5, edgeRadius = 0):
        """
        Converts this SimpleShape to a X3dDoc class and returns the result.

        id: A string that will be used to refer to this shape in X3D.
        precision: The precision that will be used for the coordinates of the
                   vertices when printing the result to an X3D or VRML formatted
                   string.
        edgeRadius: Optinal radius of the edges to be used when printing the
                    result to an X3D or VRML formatted string. If 0.0 then the
                    edges will be drawn as lines, otherwise cylinders will be
                    used (the latter will lead to a much heavier file, that will
                    be rendered much slower).
        """
        doc = X3D.Doc()
        doc.addStdMeta(self.name)
        doc.addNode(self.toX3dNode(id, precision, edgeRadius))
        return doc


    def toOffStr(self, precision = 15, info = False,
                 color_floats=False):
        """
        Converts this SimpleShape to a string in the 3D 'off' format and returns
        the result.

        precision: the precision that will be used for printing the coordinates
                   of the vertices.
        color_floats: whether to export the colours as floating point numbers
                      between 0 and 1. If False an integer 0 to 255 is used.
        """
        w = lambda a: '%s%s\n' % (s, a)
        s = ''
        s = w('OFF')
        s = w('#')
        s = w('# %s' % self.name)
        s = w('#')
        s = w('# file generated with python script by Marcel Tunnissen')
        if info:
            self.calculateSphereRadii()
            s = w('# inscribed sphere(s)    : %s' % str(self.spheresRadii.inscribed))
            s = w('# mid sphere(s)          : %s' % str(self.spheresRadii.mid))
            s = w('# circumscribed sphere(s): %s' % str(self.spheresRadii.circumscribed))
            d = self.createDihedralAngles()
            for a, Es in d.items():
                s = w('# Dihedral angle: %s rad (%s degrees) for %d edges' % (
                    glue.f2s(a, precision),
                    glue.f2s(a*Rad2Deg, precision),
                    len(Es)
                ))
                if len(Es) > 2:
                    s = w('#                 E.g. %s, %s, %s, etc' % (Es[0], Es[1], Es[2]))
            l2e = self.createEdgeLengths()
            for l, Es in l2e.items():
                s = w('# Length: %s for %d edges' % (
                    glue.f2s(l, precision), len(Es)
                ))
                if len(Es) > 2:
                    s = w('#         E.g. %s, %s, %s, etc' % (Es[0], Es[1], Es[2]))
        s = w('# Vertices Faces Edges')
        nrOfFaces = len(self.Fs)
        no_of_edges = len(self.Es) // 2
        s = w('%d %d %d' % (len(self.Vs), nrOfFaces, no_of_edges))
        s = w('# Vertices')
        for V in self.Vs:
            s = w('%s %s %s' % (
                glue.f2s(V[0], precision),
                glue.f2s(V[1], precision),
                glue.f2s(V[2], precision)
            ))
        s = w('# Sides and colours')
        # self.colorData[1] = [] : use self.colorData[0][0]
        # self.colorData[1] = [c0, c1, .. cn] where ci is an index i
        #                     self.colorData[0]
        #                     There should be as many colours as faces.
        if len(self.colorData[0]) == 1:
            oneColor = True
            color = self.colorData[0][0]
        else:
            oneColor = False
            assert len(self.colorData[1]) == len(self.colorData[1])
        def faceStr(face):
            s = ('%d  ' % (len(face)))
            for fi in face:
                s = ('%s%d ' % (s, fi))
            if color_floats:
                s = '{} {:g} {:g} {:g}'.format(s, color[0], color[1], color[2])
            else:
                s = '%s %d %d %d' % (
                        s, color[0] * 255, color[1]*255, color[2]*255)
            return s
        if oneColor:
            for face in self.Fs:
                # the lambda w didn't work: (Ubuntu 9.10, python 2.5.2)
                s = '%s%s\n' % (s, faceStr(face))
        else:
            self.createFaceNormals(normalise = True)
            for i in range(nrOfFaces):
                face = self.Fs[i]
                color = self.colorData[0][self.colorData[1][i]]
                # the lambda w didn't work: (Ubuntu 9.10, python 2.5.2)
                s = '%s%s\n' % (s, faceStr(face))
                fnStr = '%s %s %s' % (
                        glue.f2s(self.fNs[i][0], precision),
                        glue.f2s(self.fNs[i][1], precision),
                        glue.f2s(self.fNs[i][2], precision)
                    )
                if info:
                    s = w('# face normal: %s' % fnStr)
        if info:
            for i in range(no_of_edges):
                s = w('# edge: %d %d' % (self.Es[2*i], self.Es[2*i + 1]))
        s = w('# END')
        return s

    def toPsPiecesStr(self,
            faceIndices=[],
            scaling=1,
            precision=7,
            margin=1.0e5*defaultFloatMargin,
            pageSize=PS.PageSizeA4,
            suppressWarn=False
        ):
        """
        Returns a string in PS format that shows the pieces of faces that can
        be used for constructing a physical model of the object.

        The function will for each face check whether it intersects another
        face. By these intersections the face is divided into pieces. All pieces
        are printed, not only the ones that are visible from the outside.
        faceIndices: an array of faces for which the pieces should be printed.
                     Since many objects have symmetry it is not needed to
                     calculate the pieces for each face.
        scaling: All pieces in all faces are scaled by a certain factor in the
                 resulting PS string. This factor can be adjusted later in the
                 file itself (after printing the string to a file).
        precision: The precision to be used for the coordinates of the vertices.
        margin: A margin to be used when comparing floats: e.g. to recognise
                that 2 vertices have "the same" coordinates.
        """
        if faceIndices == []:
            faceIndices = list(range(len(self.Fs)))
        PsDoc = PS.doc(title = self.name, pageSize = pageSize)
        offset = 0
        debug = False
        if debug:
            print('********toPsPiecesStr********')
            for i in range(len(self.Vs)):
                print('V[', i, '] =', self.Vs[i])
        geomtypes.set_eq_float_margin(margin)
        try:
            for i in faceIndices:
                if not debug:
                    # write to stderr, since we might we writing the model
                    # itself to stdout, which might be piped to a file
                    sys.stderr.write( '\rchecking face %d (of %d)' % (
                                                    i + 1, len(faceIndices))),
                    sys.stderr.flush()
                Vs = []
                pointsIn2D = []
                Es  = []
                face = self.Fs[i]
                # find out norm
                if debug: print('face idx:', face)
                face_pl = facePlane(self.Vs, face)
                if face_pl == None: continue # not a face
                norm = face_pl.N
                if norm == None: continue # not a face.
                if debug: print('norm before', norm)
                # Find out how to rotate the faces such that the norm of the base face
                # is parallel to the z-axis to work with a 2D situation:
                # Rotate around the cross product of z-axis and norm
                # with an angle equal to the dot product of the normalised vectors.
                zAxis = vec(0, 0, 1)
                to2DAngle = math.acos(zAxis * norm)
                if eq(to2DAngle, 2 * math.pi, margin):
                    to2DAngle = 0.0
                elif eq(to2DAngle, -2 * math.pi, margin):
                    to2DAngle = 0.0
                elif eq(to2DAngle, math.pi, margin):
                    to2DAngle = 0.0
                elif eq(to2DAngle, -math.pi, margin):
                    to2DAngle = 0.0
                PsPoints = []
                if not to2DAngle == 0:
                    if debug: print('to2DAngle:', to2DAngle)
                    to2Daxis = norm.cross(zAxis)
                    if debug: print('to2Daxis:', to2Daxis)
                    Mrot = geomtypes.Rot3(angle = to2DAngle, axis = to2Daxis)
                    # add vertices to vertex array
                    for v in self.Vs:
                        Vs.append(Mrot*v)
                        pointsIn2D.append([Vs[-1][0], Vs[-1][1]])
                        #if debug: print 'added to Vs', Vs[-1]
                else:
                    Vs = self.Vs[:]
                    pointsIn2D = [[v[0], v[1]] for v in self.Vs]
                # set z-value for the z-plane, ie plane of intersection
                zBaseFace = Vs[face[0]][2]
                if debug: print('zBaseFace =', zBaseFace)
                # add edges from shares
                basePlane = facePlane(Vs, face)
                if debug: print('basePlane', basePlane)
                # split faces into
                # 1. facets that ly in the plane: baseFacets, the other facets
                #    will be intersected with these.
                # and
                # 2. facets that share one line (segment) with this plane: intersectingFacets
                #    Only save the line segment data of these.
                baseFacets = []
                Lois = []
                for intersectingFacet in self.Fs:
                    if debug:
                        print('Intersecting face[', self.Fs.index(intersectingFacet), '] =', intersectingFacet)
                        print('with face[', i, '] =', face)
                    intersectingPlane = facePlane(Vs, intersectingFacet)
                    # First check if this facet has an edge in common
                    facesShareAnEdge = False
                    if intersectingFacet == face:
                        baseFacets.append(intersectingFacet)
                        Es.append(intersectingFacet)
                        facesShareAnEdge = True
                    else:
                        l = len(intersectingFacet)
                        for p in range(l):
                            if intersectingFacet[p] in face:
                                q = p+1
                                if q == l: q = 0
                                if intersectingFacet[q] in face:
                                    pIndex = face.index(intersectingFacet[p])
                                    qIndex = face.index(intersectingFacet[q])
                                    delta =  abs(pIndex - qIndex)
                                    if (delta == 1) or (delta == len(face) - 1):
                                        facesShareAnEdge = True
                                        break

                    # line of intersection:
                    if not facesShareAnEdge:
                        Loi3D = basePlane.intersectWithPlane(intersectingPlane)
                    if facesShareAnEdge:
                        if debug: print('Intersecting face shares an edge')
                        pass
                    elif Loi3D == None:
                        if debug: print('No intersection for face')
                        # the face is parallel or lies in the plane
                        if zBaseFace == Vs[intersectingFacet[0]][2]:
                            # the face is lying in the plane, add to baseFacets
                            baseFacets.append(intersectingFacet)
                            # also add to PS array of lines.
                            Es.append(intersectingFacet)
                            if debug: print('In Plane: intersectingFacet', intersectingFacet)
                    else: # Loi3D != None:
                        if debug:
                            if debug: print('intersectingPlane', intersectingPlane)
                            if debug: print('Loi3D', Loi3D)
                        assert eq(Loi3D.v[2], 0, 100 * margin), "all intersection lines should be paralell to z = 0, but z varies with %f" % (Loi3D.v[2])
                        assert eq(Loi3D.p[2], zBaseFace, 100 * margin), "all intersection lines should ly on z==%f, but z differs %f" % (
                                        zBaseFace, zBaseFace-Loi3D.p[2]
                                    )
                        # loi2D = lineofintersection
                        loi2D = Line2D(
                                [Loi3D.p[0], Loi3D.p[1]],
                                v = [Loi3D.v[0], Loi3D.v[1]]
                            )
                        # now find the segment of loi2D within the intersectingFacet.
                        # TODO The next call is strange. It is a call to a Line2D
                        # intersecting a 3D facet. It should be a mode dedicated
                        # call. The line is in the plane of the facet and we want to
                        # know where it shares edges.
                        pInLoiFacet = loi2D.intersectWithFacet(Vs,
                                intersectingFacet, Loi3D.p[2],
                                margin, suppressWarn)
                        if debug: print('pInLoiFacet', pInLoiFacet)
                        if pInLoiFacet != []:
                            Lois.append([loi2D, pInLoiFacet, Loi3D.p[2]])
                            if debug: Lois[-1].append(self.Fs.index(intersectingFacet))
                # for each intersecting line segment:
                for loiData in Lois:
                    loi2D       = loiData[0]
                    pInLoiFacet = loiData[1]
                    if debug: print('phase 2: check iFacet nr:', loiData[-1])
                    # Now Intersect loi with the baseFacets.
                    for baseFacet in baseFacets:
                        pInLoiBase = loi2D.intersectWithFacet(Vs, baseFacet,
                                loiData[2], margin, suppressWarn)
                        if debug: print('pInLoiBase', pInLoiBase)
                        # Now combine the results of pInLoiFacet and pInLoiBase:
                        # Only keep intersections that fall within 2 segments for
                        # both pInLoiFacet and pInLoiBase.
                        facetSegmentNr = 0
                        baseSegmentNr = 0
                        nextBaseSeg = True
                        nextFacetSeg = True
                        nrOfVs = len(pointsIn2D)
                        def addPsLine(t0, t1, loi2D, nrOfVs):
                            pointsIn2D.append(loi2D.getPoint(t0))
                            pointsIn2D.append(loi2D.getPoint(t1))
                            Es.append([nrOfVs, nrOfVs+1])
                            return nrOfVs + 2
                        while (baseSegmentNr < len(pInLoiBase) // 2) and \
                            (facetSegmentNr < len(pInLoiFacet) // 2):
                            if nextBaseSeg:
                                b0 = pInLoiBase[2*baseSegmentNr]
                                b1 = pInLoiBase[2*baseSegmentNr + 1]
                                nextBaseSeg = False
                            if nextFacetSeg:
                                f0 = pInLoiFacet[2*facetSegmentNr]
                                f1 = pInLoiFacet[2*facetSegmentNr + 1]
                                nextFacetSeg = False
                            # Note that always holds f0 < f1 and b0 < b1
                            if f1 < b0 or eq(f1, b0):
                                # f0 - f1  b0 - b1
                                nextFacetSeg = True
                            elif b1 < f0 or eq(b1, f0):
                                # b0 - b1  f0 - f1
                                nextBaseSeg = True
                            elif f0 < b0 or eq(f0, b0):
                                if f1 < b1 or eq(f1, b1):
                                    # f0  b0 - f1  b1
                                    nextFacetSeg = True
                                    nrOfVs = addPsLine(b0, f1, loi2D, nrOfVs)
                                else:
                                    # f0  b0 - b1  f1
                                    nextBaseSeg = True
                                    nrOfVs = addPsLine(b0, b1, loi2D, nrOfVs)
                            else:
                                # b0<f0<b1 (and b0<f1)
                                if f1 < b1 or eq(f1, b1):
                                    # b0  f0 - f1  b1
                                    nextFacetSeg = True
                                    nrOfVs = addPsLine(f0, f1, loi2D, nrOfVs)
                                else:
                                    # b0  f0 - b1  f1
                                    nextBaseSeg = True
                                    nrOfVs = addPsLine(f0, b1, loi2D, nrOfVs)
                            if nextBaseSeg:
                                baseSegmentNr += 1
                            if nextFacetSeg:
                                facetSegmentNr += 1
                PsDoc.addLineSegments(pointsIn2D, Es, scaling, precision)
        except AssertionError as PrecisionError:
            # catching assertion errors, to be able to set back margin
            geomtypes.set_eq_float_margin(margin)
            raise
        print() # print a line feed

        # restore margin
        geomtypes.reset_eq_float_margin()

        #print PsDoc.toStr()
        return PsDoc.toStr()

    def intersectFacets(self,
            faceIndices = [],
            margin = 1.0e5*defaultFloatMargin,
            suppressWarn = False
        ):
        """
        Returns a simple shape object for which the faces do not intersect
        anymore.

        The function will for each face check whether it intersects another
        face. By these intersections the face is divided into pieces. All pieces
        will form a new shape.
        faceIndices: an optional array of faces for which the pieces should be
                     intersected. If [], then all faces will be intersected.
        margin: A margin to be used when comparing floats: e.g. to recognise
                that 2 vertices have "the same" coordinates.
        """
        # TODO:
        # Is it enough just to generate the extra edges, or should all faces be
        # divided into smaller faces?
        # I think that generating the extra edges should be sufficient, looking
        # at the use case:
        # - make transparent models. The problem with transparent models is that
        #   intersections are not shown: therefore edges are needed.
        #
        # Another use case might be interesting here as well:
        # - make prints of templates
        #
        # Though this use case has some essential differences with this
        # function
        #
        # o Actually this function needs to consider all faces, not just a
        #   subset as for printing symmetric cases.
        # o This function is not interested in whether edges ly in the same plane,
        #   while this is important for printing.
        # o on the other hand, this function needs to generate pure edges, while
        #   in the PS template polygons do not need to be split in edges.
        #
        # Because of the reasons above one would use a separate function for
        # printing.
        #
        # Then this function needs to generate only the edges that appear because of
        # extra intersections.
        #
        # Possible: Take one face, intersect all faces with higher index and
        # note extra edge(s), continue.
        #
        # Otherwise, there is a lot to think about:
        # Not easy to split a face into smaller faces. Faces need to be defined
        # in consistent direction (e.g. anti-clockwise). While defining a face,
        # always choose the edge at the left with the smallest angle (if there
        # is more than one possible edge). Note that an intersecting edge has 2
        # directions and note that digons can appear while intersecting (even
        # outside an existing face, since that one can endup inside, if a
        # coplanar face is added in the end).
        # This is a lot so before you begin with that look at std methods, e.g.
        # S Fortune - Proceedings of the third ACM symposium on Solid modeling and, 1995 - portal.acm.org Polyhedral modelling with exact arithmetic
        #

        if faceIndices == []:
            faceIndices = list(range(len(self.Fs)))
        debug = True
        debug = False
        if debug: print('********intersectFacets********')
        margin, geomtypes.eq_float_margin = geomtypes.eq_float_margin, margin
        for i in faceIndices:
            # TODO: problem Vs is calculated per face...
            #       clean up later...?
            Vs = []
            pointsIn2D = []
            Es  = []
            face = self.Fs[i]
            assert len(face) > 2, 'a face should at least be a triangle'
            # find out norm
            norm = PPPnorm(
                    self.Vs[face[0]],
                    self.Vs[face[1]],
                    self.Vs[face[2]]
                )
            if debug: print('norm before', norm)
            # Find out how to rotate the faces such that the norm of the base face
            # is parallel to the z-axis to work with a 2D situation:
            # Rotate around the cross product of z-axis and norm
            # with an angle equal to the dot product of the normalised vectors.
            zAxis = vec(0, 0, 1)
            to2DAngle = math.acos(zAxis * norm)
            PsPoints = []
            if to2DAngle != 0:
                to2Daxis = norm.cross(zAxis)
                Mrot = geomtypes.Rot3(angle = to2DAngle, axis = to2Daxis)
                # add vertices to vertex array
                for v in self.Vs:
                    Vs.append(Mrot*vec(v))
                    pointsIn2D.append([Vs[-1][0], Vs[-1][1]])
                    #if debug: print 'added to Vs', Vs[-1]
            else:
                Vs = self.Vs[:]
                pointsIn2D = [[v[0], v[1]] for v in self.Vs]
            # set z-value for the z-plane, ie plane of intersection
            zBaseFace = Vs[face[0]][2]
            if debug: print('zBaseFace =', zBaseFace)
            # add edges from shares
            basePlane = Plane(
                    Vs[face[0]],
                    Vs[face[1]],
                    Vs[face[2]]
                )
            if debug: print('basePlane', basePlane)
            # split faces into
            # 1. facets that ly in the plane: baseFacets, the other facets
            #    will be intersected with these.
            # and
            # 2. facets that share one line (segment) with this plane: intersectingFacets
            #    Only save the line segment data of these.
            baseFacets = []
            Lois = []
            for intersectingFacet in self.Fs:
                if debug:
                    print('Intersecting face[', self.Fs.index(intersectingFacet), '] =', intersectingFacet)
                    print('with face[', i, '] =', face)
                intersectingPlane = Plane(
                        Vs[intersectingFacet[0]],
                        Vs[intersectingFacet[1]],
                        Vs[intersectingFacet[2]]
                    )
                # First check if this facet has at least one edge in common
                facesShareAnEdge = False
                # if this facet has the face itself:
                if intersectingFacet == face:
                    baseFacets.append(intersectingFacet)
                    Es.append(intersectingFacet)
                    facesShareAnEdge = True
                else:
                    # if this facet has one edge in common (edge [p, q])
                    nrOfVsIntersectingFacet = len(intersectingFacet)
                    for p in range(nrOfVsIntersectingFacet):
                        if intersectingFacet[p] in face:
                            q = p+1
                            if q == nrOfVsIntersectingFacet: q = 0
                            if intersectingFacet[q] in face:
                                pIndex = face.index(intersectingFacet[p])
                                qIndex = face.index(intersectingFacet[q])
                                delta =  abs(pIndex - qIndex)
                                if (delta == 1) or (delta == len(face) - 1):
                                    facesShareAnEdge = True
                                    break

                # line of intersection:
                # TODO: can one optimise a bit by comparing max(X,Y, or Z)
                # values. if the MAX(z) of intersecting facet < MIN(z)
                # baseFacet then no intersection.
                if facesShareAnEdge:
                    if debug: print('Intersecting face shares an edge')
                else:
                    Loi3D = basePlane.intersectWithPlane(intersectingPlane)
                    if Loi3D == None:
                        if debug: print('No intersection for face')
                        # the face is parallel or lies in the plane
                        if zBaseFace == Vs[intersectingFacet[0]][2]:
                            # the face is lying in the plane, add to baseFacets
                            baseFacets.append(intersectingFacet)
                            # also add to PS array of lines.
                            Es.append(intersectingFacet)
                            print('In Plane: intersectingFacet', intersectingFacet)
                    else: # Loi3D != None:
                        if debug:
                            print('intersectingPlane', intersectingPlane)
                            print('Loi3D', Loi3D)
                        assert eq(Loi3D.v[2], 0, margin), "all intersection lines should be paralell to z = 0, but z varies with %f" % (Loi3D.v[2])
                        assert eq(Loi3D.p[2], zBaseFace, margin), "all intersection lines should ly on z==%f, but z differs %f" % (
                                        zBaseFace, zBaseFace-Loi3D.p[2]
                                    )
                        # loi2D = lineofintersection
                        loi2D = Line2D(
                                [Loi3D.p[0], Loi3D.p[1]],
                                v = [Loi3D.v[0], Loi3D.v[1]]
                            )
                        # now find the segment of loi2D within the intersectingFacet.
                        # TODO The next call is strange. It is a call to a Line2D
                        # intersecting a 3D facet. It should be a mode dedicated
                        # call. The line is in the plane of the facet and we want to
                        # know where it shares edges.
                        pInLoiFacet = loi2D.intersectWithFacet(Vs,
                            intersectingFacet, Loi3D.p[2], margin, suppressWarn)
                        if debug: print('pInLoiFacet', pInLoiFacet)
                        if pInLoiFacet != []:
                            Lois.append([loi2D, pInLoiFacet, Loi3D.p[2]])
                            if debug: Lois[-1].append(self.Fs.index(intersectingFacet))

            # Now that all facets are checked for intersections,
            # find a gravity point for settings x and y offset (TODO: PS only)
            nrOfVs = 0
            xOffset = 0.0
            yOffset = 0.0
            for face in baseFacets:
                for i in face:
                    nrOfVs = nrOfVs + 1
                    xOffset += Vs[i][0]
                    yOffset += Vs[i][1]
            xOffset = xOffset / nrOfVs
            yOffset = yOffset / nrOfVs
            # intersect the line segments with the existing sides of the
            # basefacets.
            # for each intersecting line segment:
            for loiData in Lois:
                loi2D       = loiData[0]
                pInLoiFacet = loiData[1]
                if debug: print('phase 2: check iFacet nr:', loiData[-1])
                # Now Intersect loi with the baseFacets.
                for baseFacet in baseFacets:
                    pInLoiBase = loi2D.intersectWithFacet(Vs, baseFacet,
                        loiData[2], margin, suppressWarn)
                    if debug: print('pInLoiBase', pInLoiBase)
                    # Now combine the results of pInLoiFacet and pInLoiBase:
                    # Only keep intersections that fall within 2 segments for
                    # both pInLoiFacet and pInLoiBase.
                    facetSegmentNr = 0
                    baseSegmentNr = 0
                    nextBaseSeg = True
                    nextFacetSeg = True
                    nrOfVs = len(pointsIn2D)
                    def addPsLine(t0, t1, loi2D, nrOfVs):
                        pointsIn2D.append(loi2D.getPoint(t0))
                        pointsIn2D.append(loi2D.getPoint(t1))
                        Es.append([nrOfVs, nrOfVs+1])
                        return nrOfVs + 2
                    while (baseSegmentNr < len(pInLoiBase)/2) and \
                        (facetSegmentNr < len(pInLoiFacet)/2):
                        if nextBaseSeg:
                            b0 = pInLoiBase[2*baseSegmentNr]
                            b1 = pInLoiBase[2*baseSegmentNr + 1]
                            nextBaseSeg = False
                        if nextFacetSeg:
                            f0 = pInLoiFacet[2*facetSegmentNr]
                            f1 = pInLoiFacet[2*facetSegmentNr + 1]
                            nextFacetSeg = False
                        # Note that always holds f0 < f1 and b0 < b1
                        if f1 < b0 or eq(f1, b0):
                            # f0 - f1  b0 - b1
                            nextFacetSeg = True
                        elif b1 < f0 or eq(b1, f0):
                            # b0 - b1  f0 - f1
                            nextBaseSeg = True
                        elif f0 < b0 or eq(f0, b0):
                            if f1 < b1 or eq(f1, b1):
                                # f0  b0 - f1  b1
                                nextFacetSeg = True
                                nrOfVs = addPsLine(b0, f1, loi2D, nrOfVs)
                            else:
                                # f0  b0 - b1  f1
                                nextBaseSeg = True
                                nrOfVs = addPsLine(b0, b1, loi2D, nrOfVs)
                        else:
                            # b0<f0<b1 (and b0<f1)
                            if f1 < b1 or eq(f1, b1):
                                # b0  f0 - f1  b1
                                nextFacetSeg = True
                                nrOfVs = addPsLine(f0, f1, loi2D, nrOfVs)
                            else:
                                # b0  f0 - b1  f1
                                nextBaseSeg = True
                                nrOfVs = addPsLine(f0, b1, loi2D, nrOfVs)
                        if nextBaseSeg:
                            baseSegmentNr += 1
                        if nextFacetSeg:
                            facetSegmentNr += 1
            # scale offsets:
            xOffset = scaling * xOffset
            yOffset = scaling * yOffset
            # add offset to middle of A4: 577 x 842
            xOffset += 594 / 2
            yOffset += 842 / 2
            # correct for internal 100 0 translate:
            # TODO rewrite func, for this shape
            xOffset -= 100
            PsDoc.addPageStr(
                    facesToPs(
                        pointsIn2D, Es, scaling, xOffset,
                        yOffset, precision = precision
                    )
                )

        # restore margin
        geomtypes.eq_float_margin = margin

    def getDome(self, level = 2):
        shape = None
        # check if level is in supported domain
        if level < 1 or level > 2: return shape
        fprop = self.getFaceProperties()
        cols = fprop['colors']
        Vs = self.Vs[:]
        nrOrgVs = len(self.Vs)
        try: G = self.fGs
        except AttributeError:
            self.calculateFacesG()
        try: outSphere = self.spheresRadii.circumscribed
        except AttributeError:
            self.calculateSphereRadii()
            outSphere = self.spheresRadii.circumscribed
        R = reduce(max, iter(outSphere.keys()))
        Fs = []
        colIndices = []
        def addPrjVs(xVs):
            # func global Vs, R
            Vs.extend([R * x.normalize() for x in xVs])
        def domiseLevel1(f, i):
            # return xFs
            # func global nrOrgVs, cols
            # assumes that the gravity centres will be added to Vs in face order
            # independently.
            l = len(f)
            return [[i+nrOrgVs, f[j], f[(j+1) % l]] for j in range(l)]
        def domiseLevel2(f):
            # f can only be a triangle: no check
            # return (xVs, xFs) tuple
            # func global: Vs
            xVs = []
            xVs = [(Vs[f[i]] + Vs[f[(i+1) % 3]]) / 2  for i in range(3)]
            vOffset = len(Vs)
            xFs = [
                [vOffset, vOffset + 1, vOffset + 2],
                [f[0]   , vOffset    , vOffset + 2],
                [f[1]   , vOffset + 1, vOffset    ],
                [f[2]   , vOffset + 2, vOffset + 1]
            ]
            return (xVs, xFs)

        for f, i in zip(self.Fs, self.FsRange):
            if level == 1:
                xFs = domiseLevel1(f, i)
                # add the gravity centres as assumed by domiseLevel1:
                addPrjVs(self.fGs)
            else:
                l = len(f)
                if l == 3:
                    xVs, xFs = domiseLevel2(f)
                    addPrjVs(xVs)
                elif l > 3:
                    tmpFs = domiseLevel1(f, i)
                    # add the gravity centres as assumed by domiseLevel1:
                    addPrjVs(self.fGs)
                    xFs   = []
                    for sf in tmpFs:
                        xVs, sxFs = domiseLevel2(sf)
                        addPrjVs(xVs)
                        xFs.extend(sxFs)
            Fs.extend(xFs)
            colIndices.extend([cols[1][i] for j in range(len(xFs))])
        shape = SimpleShape(Vs, Fs, [], colors = (cols[0], colIndices))
        shape.recreateEdges()
        return shape

class CompoundShape(base.Orbitit):
    """
    The class describes a shape that is the result of combining more than one
    SimpleShapes. The resulting shape can be treated as one, e.g. it can be
    exported as one 'OFF' file.
    """
    def __init__(self, simpleShapes, name = "CompoundShape"):
        """
        simpleShapes: an array of SimpleShape objects of which the shape is a
        compound.
        """
        self.name = name
        self.setShapes(simpleShapes)

    def __repr__(self):
        """
        Returns a python string that can be interpreted by Python for the shape
        """
        if len(self.shapeElements) == 1:
            return repr(self.shapeElements[0])
        else:
            s = indent.Str(
                '%s(\n' % base.find_module_class_name(self.__class__, __name__))
            s = s.add_incr_line('simpleShapes=[')
            s.incr()
            s = s.glue_line(',\n'.join(
                repr(shape).reindent(s.indent) for shape in self.shapeElements)
            )
            s = s.add_decr_line('],')
            s = s.add_line('name="%s"' % self.name)
            s = s.add_decr_line(')')
            if __name__ != '__main__':
                s = s.insert('%s.' % __name__)
            return s

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        return {
            'class': base.class_to_json[self.__class__],
            "data": {
                "name": self.name,
                "shapes": [s.repr_dict for s in self.shapes],
            }
        }

    @classmethod
    def from_dict_data(cls, data):
        return cls(
            shapes=[base.json_to_class[s["class"]].from_json_dict(s) for s in data["shapes"]],
            name=data["name"],
        )

    def saveFile(self, fd):
        """
        Save a shape in a file descriptor

        The caller still need to close the filde descriptor afterwards
        """
        saveFile(fd, self)

    def addShape(self, shape):
        """
        Add shape 'shape' to the current compound.
        """
        shape.gl.alwaysSetVertices = True
        self.shapeElements.append(shape)
        if len(self.shapeElements) > 1:
            self.shapeElements[-1].generateNormals =\
                self.shapeElements[0].generateNormals
        self.merge_needed = True

    @property
    def shapes(self):
        return self.shapeElements

    def gl_alwaysSetVertices(self, do):
        for shape in self.shapeElements:
            shape.gl_alwaysSetVertices(do)

    def setShapes(self, simpleShapes):
        """
        Set the shapes all at once.

        Note: you need to make sure yourself to have the generateNormals set
        consistently for all shapes.
        """
        self.shapeElements = simpleShapes
        self.gl_alwaysSetVertices(True)
        self.merge_needed = True

    def merge_shapes(self):
        """Using the current array of shapes as defined in shapeElements,
        initialise this object as a simple Shape.

        The function will create one Vs, Fs, and Es from the current definition
        of shapeElements and will initialise this object as a SimpleShape.
        """
        Vs = []
        Fs = []
        Es = []
        Ns = []
        colorDefs = []
        colorIndices = []
        for s in self.shapeElements:
            VsOffset  = len(Vs)
            colOffset = len(colorDefs)
            s = s.simple_shape
            # Apply shape orientation here, needed, since the can be different
            # for the various shapes
            for v in s.Vs:
                Vs.append(s.orientation * v)
            for v in s.Ns:
                Ns.append(s.orientation * v)
            # offset all faces:
            Fs.extend([[ i+VsOffset for i in f] for f in s.Fs])
            Es.extend([ i+VsOffset for i in s.Es])
            colorDefs.extend(s.colorData[0])
            colorIndices.extend([ i+colOffset for i in s.colorData[1]])
        self.merged_shape = SimpleShape(
                Vs = Vs, Fs = Fs, Es = Es, Ns = Ns,
                colors = (colorDefs, colorIndices)
            )
        self.merge_needed = False

    @property
    def simple_shape(self):
        """Return the compound shape as a simple merged and flat shape
        """
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape

    def cleanShape(self, precision):
        """Return a new shape for which vertices are merged and degenerated faces are deleted.

        The shape will not have any edges.
        """
        self.simple_shape.cleanShape(precision)

    def glDraw(self):
        """Draws the compound shape as compound shape

        If you want to draw it as one, draw the SimpleShape instead
        """
        for shape in self.shapeElements:
            shape.glDraw()

    def recreateEdges(self):
        for shape in self.shapeElements:
            shape.recreateEdges()
        self.merge_needed = True

    def setVertexProperties(self, dictPar = None, **kwargs):
        """Set the vertex properties for a whole compound shape at once

        Vs: This is an array of Vs. One Vs array for each shape element
        Ns: This is an array of Ns. One Ns array for each shape element
        radius: one radius that is valid for all shape elements
        color: one vertex color that is valid for all shape elements

        See the same function in SimpleShape.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Vs' in dict and dict['Vs'] != None:
                Vs = dict['Vs']
            else:
                Vs = [None for shape in self.shapeElements]
            if 'Ns' in dict and dict['Ns'] != None:
                Ns = dict['Ns']
            else:
                Ns = [None for shape in self.shapeElements]
            if 'radius' in dict:
                radius = dict['radius']
            else:
                radius = None
            if 'color' in dict:
                color = dict['color']
            else:
                color = None
        assert len(Vs) == len(self.shapeElements)
        assert len(Ns) == len(self.shapeElements)
        for i in range(len(self.shapeElements)):
            self.shapeElements[i].setVertexProperties(
                Vs = Vs[i], Ns = Ns[i], radius = radius, color = color
            )
        self.merge_needed = True

    def getVertexProperties(self):
        """Return a dictionary of the vertex properties of the compound

        See setVertexProperties what to expect.
        """
        # Note: cannot use the megedShape, since the Vs is not an array of Vs
        d = self.shapeElements[0].getVertexProperties()
        return {
            'Vs': self.Vs,
            'radius': d['radius'],
            'color': d['color'],
            'Ns': self.Ns
        }

    def setEdgeProperties(self, dictPar = None, **kwargs):
        """Set the edge properties for a whole compound shape at once

        Es: This is an array of Es. One Es array for each shape element
        radius: one radius that is valid for all shape elements
        color: one vertex color that is valid for all shape elements

        See the same function in SimpleShape.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Es' in dict and dict['Es'] != None:
                Es = dict['Es']
            else:
                Es = [None for shape in self.shapeElements]
            if 'radius' in dict:
                radius = dict['radius']
            else:
                radius = None
            if 'color' in dict:
                color = dict['color']
            else:
                color = None
            if 'drawEdges' in dict:
                drawEdges = dict['drawEdges']
            else:
                drawEdges = None
        for i in range(len(self.shapeElements)):
            self.shapeElements[i].setEdgeProperties(
                Es = Es[i], radius = radius, color = color, drawEdges = drawEdges
            )
        self.merge_needed = True

    def getEdgeProperties(self):
        """Return a dictionary of the edge properties of the compound

        See setEdgeProperties what to expect.
        """
        d = self.shapeElements[0].getEdgeProperties()
        return {
            'Es': self.Es,
            'radius': d['radius'],
            'color': d['color'],
            'drawEdges': d['drawEdges']
        }

    def setFaceProperties(self, dictPar = None, **kwargs):
        """Set the face properties for a whole compound shape at once

        Fs: This is an array of Es. One Es array for each shape element
        colors: This is an array of colors. One colors set for each shape
                element.
        drawFaces: one drawFaces setting that is valid for all shape elements

        See the same function in SimpleShape.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Fs' in dict and dict['Fs'] != None:
                Fs = dict['Fs']
            else:
                Fs = [None for shape in self.shapeElements]
            if 'colors' in dict and dict['colors'] != None:
                colors = dict['colors']
            else:
                colors = [None for shape in self.shapeElements]
            if 'drawFaces' in dict:
                drawFaces = dict['drawFaces']
            else:
                drawFaces = None
        for i in range(len(self.shapeElements)):
            self.shapeElements[i].setFaceProperties(
                Fs = Fs[i], colors = colors[i], drawFaces = drawFaces
            )
        self.merge_needed = True

    def getFaceProperties(self):
        """Return a dictionary of the face properties of the compound

        See setFaceProperties what to expect.
        """
        d = self.shapeElements[0].getFaceProperties()
        return {
            'Fs': self.Fs,
            'colors': self.colorData,
            'drawFaces': d['drawFaces']
        }

    @property
    def dimension(self):
        return self.shapeElements[0].dimension

    @property
    def Vs(self):
        return [shape.Vs for shape in self.shapeElements]

    @property
    def Ns(self):
        return [shape.Ns for shape in self.shapeElements]

    @property
    def Es(self):
        return [shape.Es for shape in self.shapeElements]

    @property
    def Fs(self):
        return [shape.Fs for shape in self.shapeElements]

    @property
    def colorData(self):
        return [shape.colorData for shape in self.shapeElements]

    @property
    def generateNormals(self):
        return self.shapeElements[0].generateNormals

    def toOffStr(self, precision = 15, info = False):
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.toOffStr(precision, info)

    def toPsPiecesStr(self,
            faceIndices = [],
            scaling = 1,
            precision = 7,
            margin = 1.0e5*defaultFloatMargin,
            pageSize = PS.PageSizeA4,
            suppressWarn = False
    ):
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.toPsPiecesStr(
            faceIndices, scaling, precision, margin, pageSize, suppressWarn)

    def toX3dDoc(self, id = 'SISH', precision = 5, edgeRadius = 0):
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.toX3dDoc(id, precision, edgeRadius)

    def getDome(self, level = 2):
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.getDome(level)

class SymmetricShape(CompoundShape):
    """
    The class describes simple shapes that have a base shape that is reused by
    some transformations. They can be expressed by a subset of all vertices,
    edges and faces. The isometries of the shape are then used to reproduce the
    complete shape.
    """
    def __init__(self,
        Vs,
        Fs,
        Es=[],
        Ns=[],
        # TODO: remove double array: the opposite symmetries are gone. Also update the docstrin.
        colors=[([], [])],
        isometries=[E],
        name="SymmetricShape",
        recreateEdges=True,
        orientation=None,
    ):
        """
        Vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        Fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        Es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        Ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by glDraw
        colors: optional array parameter describing the colours. Each element
                consists of a tuple similar to the the 'colors' parameter from
                SimpleShape; see the __init__ function of that class. The tuples
                will be used to divide the colours over the different elements
                of the orbit, first for all the direct isometries, then the
                opposite. The array should at least contain one tuple to specify
                the base element.
        isometries: a list of all isometries that are needed to reproduce all
            parts of the shape can can be transformed from the specified base
            element through an isometry.
        name: a string identifier representing the model.
        orientation: orientation of the base shape. This is an isometry operation.
        """
        # this is before creating the base shape, since it check "colors"
        self.base_shape = SimpleShape(
            Vs, Fs, Es,
            Ns=Ns,
            colors=colors[0],
            orientation=orientation,
        )
        if recreateEdges:
            self.base_shape.recreateEdges()
        CompoundShape.__init__(self, [self.base_shape], name = name)
        self.setFaceColors(colors)
        self.isometries = isometries
        self.order = len(isometries)
        self.needs_apply_isoms = True
        self.show_base_only = False

    def __repr__(self):
        # comment out class name, see comment at __fix_repr__ below:
        #s = indent.Str('%s(\n' % base.find_module_class_name(self.__class__, __name__))
        s = indent.Str('SymmetricShape(\n')
        s = s.add_incr_line('Vs=[')
        s.incr()
        try:
            s = s.glue_line(',\n'.join(
                indent.Str(repr(v)).reindent(s.indent) for v in self.base_shape.Vs)
            )
        except AttributeError:
            print('ERROR: Are you sure the vertices are all of type geomtypes.Vec3?')
            raise
        s = s.add_decr_line('],')
        s = s.add_line('Fs=[')
        s.incr()
        s = s.glue_line(',\n'.join(
            indent.Str(repr(f)).reindent(s.indent) for f in self.base_shape.Fs)
        )
        s = s.add_decr_line('],')
        if self.base_shape.Es != []:
            s = s.add_line('Es=%s,' % repr(self.base_shape.Es))
        if self.base_shape.Ns != []:
            s = s.add_incr_line('Ns=[')
            s.incr()
            try:
                s = s.glue_line(',\n'.join(
                    repr(n).reindent(s.indent) for n in self.base_shape.Ns)
                )
            except AttributeError:
                print('ERROR: Are you sure the normals are all of type geomtypes.Vec3?')
                raise
            s = s.add_decr_line('],')
        s = s.add_line('colors=[')
        s.incr()
        cols = self.getFaceColors()
        s = s.glue_line(',\n'.join(
            indent.Str(repr(c)).reindent(s.indent) for c in cols)
        )
        s = s.add_decr_line('],')
        if self.isometries != None:
            s = s.add_line('isometries=[')
            s.incr()
            s = s.glue_line(
                ',\n'.join(
                    indent.Str(repr(i)).reindent(s.indent) for i in self.isometries
                )
            )
            s = s.add_decr_line('],')
        s = s.add_line("name='%s'," % self.name)
        s = s.glue_line(
            indent.Str(
                'orientation=%s' % repr(self.base_shape.orientation)
            ).reindent(s.indent)
        )
        s = s.add_decr_line(')')
        if __name__ != '__main__':
            s = s.insert('%s.' % __name__)
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        # Note that orientation IS essential here.
        return {
            'class': base.class_to_json[self.__class__],
            'data': {
                'name': self.name,
                'vs': self.base_shape.Vs,
                'fs': self.base_shape.Fs,
                'cols': self.shape_colors,
                'orientation': self.base_shape.orientation.repr_dict,
                'isometries': [i.repr_dict for i in self.isometries],
            },
        }

    def merge_shapes(self):
        if self.show_base_only:
            # assuming that the base shape is a simple shape:
            self.merged_shape = self.base_shape
            self.merge_needed = False
        elif self.needs_apply_isoms:
            self.apply_isoms()

        CompoundShape.merge_shapes(self)

    def setFaceColors(self, colors):
        """
        Check and set the face colours and and save their properties.
        """
        if colors == [([], [])]:
            colors = [([rgb.gray95[:]], [])]
        assert len(colors) > 0, 'colors should have at least one element'
        assert len(colors[0]) == 2, \
            'a colors element should be a tuple of 2 elements: (colors, fColors)'
        self.shape_colors = colors
        self.nrOfShapeColorDefs = len(colors)
        self.merge_needed = True
        self.needs_apply_isoms = True

    def getFaceColors(self):
        return self.shape_colors

    def applyColors(self):
        """
        Divide the shape colors over the isometries and re-assign class field.
        """
        if (self.nrOfShapeColorDefs != self.order):
            if self.nrOfShapeColorDefs == 1:
                colorDataPerShape = [
                        self.shape_colors[0] for i in range(self.order)
                    ]
            elif self.nrOfShapeColorDefs < self.order:
                div = self.order / self.nrOfShapeColorDefs
                mod = self.order % self.nrOfShapeColorDefs
                colorDataPerShape = []
                for i in range(div):
                    colorDataPerShape.extend(self.shape_colors)
                colorDataPerShape.extend(self.shape_colors[:mod])
            else:
                colorDataPerShape = self.shape_colors[:self.order],
            self.shape_colors = colorDataPerShape
        self.nrOfShapeColorDefs = len(self.shape_colors)
        assert (self.nrOfShapeColorDefs == self.order), '%d != %d' % (
            self.nrOfShapeColorDefs, self.order)

    def apply_isoms(self):
        """
        Apply the isometry operations for the current properties, like Vs and
        colour settings.

        This will create all the individual shapes.
        """

        if len(self.shape_colors) != self.order:
            self.applyColors()
        shapes = [
            SimpleShape(
                self.base_shape.Vs,
                self.base_shape.Fs,
                self.base_shape.Es,
                Ns = self.base_shape.Ns,
                colors = self.shape_colors[i],
                orientation = isom * self.base_shape.orientation
            )
            for i, isom in enumerate(self.isometries)
        ]
        self.setShapes(shapes)
        self.needs_apply_isoms = False

    def setVs(self, Vs):
        assert len(Vs) == len(self.base_shape.Vs)
        self.base_shape.setVertexProperties(Vs = Vs)
        self.merge_needed = True
        self.needs_apply_isoms = True

    def setBaseOrientation(self, orientation):
        self.base_shape.orientation = orientation
        self.needs_apply_isoms = True

    def setBaseVertexProperties(self, dictPar = None, **kwargs):
        """
        Set the vertices and how/whether vertices are drawn in OpenGL for the
        base element.

        Accepted are the optional (keyword) parameters:
        - Vs,
        - radius,
        - color.
        - Ns.
        Check SimpleShape.setVertexProperties for more details.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            Vs = None
            try: Vs = dict['Vs']
            except KeyError: pass
            Ns = None
            try: Ns = dict['Ns']
            except KeyError: pass
            if not (Vs == None and Ns == None):
                self.base_shape.setVertexProperties(Vs = Vs, Ns = Ns)
                self.needs_apply_isoms = True
            radius = None
            try: radius = dict['radius']
            except KeyError: pass
            color = None
            try: color = dict['color']
            except KeyError: pass
            if not (radius == None and color == None):
                self.setVertexProperties(radius = radius, color = color)
        else:
            print('oops')

    def getBaseVertexProperties(self):
        """
        Get the vertex properties of the base element.

        See SimpleShape.getVertexProperties for more.
        """
        return self.base_shape.getVertexProperties()

    def setBaseEdgeProperties(self, dictPar = None, **kwargs):
        """
        Specify the edges and set how they are drawn in OpenGL.

        Accepted are the optional (keyword) parameters:
          - Es,
          - radius,
          - color,
          - drawEdges.
        Check SimpleShape.setEdgeProperties for more details.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Es' in dict and dict['Es'] != None:
                self.base_shape.setEdgeProperties(Es = dict['Es'])
                self.needs_apply_isoms = True
            radius = None
            try: radius = dict['radius']
            except KeyError: pass
            color = None
            try: color = dict['color']
            except KeyError: pass
            drawEdges = None
            try: drawEdges = dict['drawEdges']
            except KeyError: pass
            if not (radius == None and color == None and drawEdges == None):
                self.setEdgeProperties(
                    radius = radius, color = color, drawEdges = drawEdges
                )
                CompoundShape.setEdgeProperties(self,
                        radius = radius, color = color, drawEdges = drawEdges)
                print('radius', radius)
                self.merge_needed = True

    def getBaseEdgeProperties(self):
        """
        Get the edge properties of the base element.

        See SimpleShape.getEdgeProperties for more.
        """
        return self.base_shape.getEdgeProperties()

    def setBaseFaceProperties(self, dictPar = None, **kwargs):
        """
        Define the properties of the faces for the base element.

        Accepted are the optional (keyword) parameters:
          - Fs,
          - colors,
          - drawFaces.
        Check SimpleShape.setFaceProperties for more details.
        """
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Fs' in dict and dict['Fs'] != None:
                self.base_shape.setFaceProperties(Fs = dict['Fs'])
                self.needs_apply_isoms = True
            if 'colors' in dict and dict['colors'] != None:
                self.setFaceColors([dict['colors']])
                # taken care of by the function above:
                # self.merge_needed = True
            if 'drawFaces' in dict and dict['drawFaces'] != None:
                self.setEnableDrawFaces(dict['drawFaces'])

    def getBaseFaceProperties(self):
        """
        Get the face properties of the base element.

        See SimpleShape.getFaceProperties for more.
        """
        return self.base_shape.getFaceProperties()

    def glDraw(self):
        if self.show_base_only:
            self.base_shape.glDraw()
        else:
            if self.needs_apply_isoms:
                self.apply_isoms()
            CompoundShape.glDraw(self)

    def toPsPiecesStr(self,
            faceIndices=[],
            scaling=1,
            precision=7,
            margin=1.0e5*defaultFloatMargin,
            pageSize=PS.PageSizeA4,
            suppressWarn=False
        ):
        if self.merge_needed:
            self.merge_shapes()
        if faceIndices == []:
            # no need to print all faces in orbited, because of symmetry
            faceIndices = list(range(len(self.base_shape.Fs)))
        return self.simple_shape.toPsPiecesStr(
            faceIndices, scaling, precision, margin, pageSize, suppressWarn)

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

    def __init__(self,
        Vs, Fs, Es = [], Ns = [],
        finalSym = isometry.E, stabSym = isometry.E,
        colors = [],
        name = "OrbitShape",
        recreateEdges = True,
        quiet=False
    ):
        """
        Vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        Fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        Es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        Ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by glDraw
        finalSym: the resulting symmetry of the shape.
        stabSym: the symmetry of the stabiliser, which is a subgroup of finalSym

        As an example: a square is used to define a cube. The square has a D4C4
        symmetry and the cube S4xI. The former is used as stabSym and the latter
        as finalSym.
        The following parameters can be used:
        with v = lambda x, y, z: geomtypes.Vec3([x, y, z])
        Vs = [v(1, 1, 1), v(1, -1, 1), v(1, -1, -1), v(1, 1, -1)] and
        Fs = [[0, 1, 2, 3]]
        finalSym = S4xI(setup = {'o4axis0': v(0, 0, 1), 'o4axis1': v(0, 1, 0)})
        stabSym = D4C4(setup = {'axis_n': v(1, 0, 0), 'normal_r': v(0, 1, 0)})
        colors: the colours per isometry. (use [] for none)
        """
        try: fsQuotientSet = finalSym  / stabSym
        except isometry.ImproperSubgroupError:
            print("ERROR: Stabiliser not a subgroup of final symmetry")
            raise
        FsOrbit = [coset.get_one() for coset in fsQuotientSet]
        if not quiet:
            print('Applying an orbit of order %d' % len(FsOrbit))
        super().__init__(
            Vs,
            Fs,
            Es,
            Ns,
            isometries=FsOrbit,
            name=name,
            recreateEdges=recreateEdges
        )
        self.finalSym = finalSym
        self.stabSym = stabSym
        if colors != []:
            self.setFaceColors(colors)

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        return {
            'class': base.class_to_json[self.__class__],
            'data': {
                'name': self.name,
                'vs': self.Vs,
                'fs': self.Fs,
                'cols': self.shape_colors,
                'final_sym': self.finalSym.repr_dict,
                'stab_sym': self.stabSym.repr_dict,
            },
        }

    def __repr__(self):
        # This repr should be fixed, since you cannot be sure in which order the
        # isometry operation will be printed (there is no ordering in a Set.
        # This requires a more user friendly class interface for the user:
        # provide an array of colours and a symmetry (and index) on which the
        # colouring is based. For now fall back on the parental repr.
        s = indent.Str(f"{base.find_module_class_name(self.__class__, __name__)}(\n")
        s = s.add_incr_line('Vs=[')
        s.incr()
        try:
            s = s.glue_line(',\n'.join(
                indent.Str(repr(v)).reindent(s.indent) for v in self.base_shape.Vs)
            )
        except AttributeError:
            print('ERROR: Are you sure the vertices are all of type geomtypes.Vec3?')
            raise
        s = s.add_decr_line('],')
        s = s.add_line('Fs=[')
        s.incr()
        s = s.glue_line(',\n'.join(
            indent.Str(repr(f)).reindent(s.indent) for f in self.base_shape.Fs)
        )
        s = s.add_decr_line('],')
        if self.base_shape.Es != []:
            s = s.add_line('Es=%s,' % repr(self.base_shape.Es))
        if self.base_shape.Ns != []:
            s = s.add_incr_line('Ns=[')
            s.incr()
            try:
                s = s.glue_line(',\n'.join(
                    repr(n).reindent(s.indent) for n in self.base_shape.Ns)
                )
            except AttributeError:
                print('ERROR: Are you sure the normals are all of type geomtypes.Vec3?')
                raise
            s = s.add_decr_line('],')
        s = s.add_line('colors=[')
        s.incr()
        cols = self.getFaceColors()
        s = s.glue_line(',\n'.join(
            indent.Str(repr(c)).reindent(s.indent) for c in cols)
        )
        s = s.add_decr_line('],')
        s = s.add_line('finalSym=')
        s.incr()
        s = s.glue_line((repr(self.finalSym) + ",").reindent(s.indent))
        s.decr()
        s = s.add_line('stabSym=')
        s.incr()
        s = s.glue_line((repr(self.stabSym) + ",").reindent(s.indent))
        s.decr()
        s = s.add_line("name='%s'," % self.name)
        s = s.add_decr_line(')')
        if __name__ != '__main__':
            s = s.insert('%s.' % __name__)
        return s

        return s
        s = '%sfinalSym = %s,\n  stabSym = %s,\n  ' % (
                s,
                repr(self.finalSym),
                repr(self.stabSym)
            )
        cols = self.getFaceColors()
        s = '%scolors = [\n  ' % (s)
        for subShapeCols in cols:
            s = '%s  %s,\n  ' % (s, repr(subShapeCols))
        s = '%s],\n  ' % (s)
        s = '%sname = "%s"\n' % (s, self.name)
        s = '%s)\n' % (s)
        if __name__ != '__main__':
            s = '%s.%s' % (__name__, s)
        return s

    def setColours(self, colours, stabSym):
        """
        Use the colours as specied and divide them according stabSym

        colours: an array with rgb colour defs.
        stabSym: the colours will be divided in a symmetric way, ie. in such a
                 way that the base parts with the same colour have the symmetry
                 stabSym. For this to happen:
                 1. the following is required:
                    - stabSym is a subgroup of finalSym at object creation.
                 2. the following is usually the case:

                 An example of the usual case. A square is used to define a
                 cube as explained in __init__.
                 former is used as stabSym at object creation and the latter as
                 finalSym.
                 CONTINUE here: testing cube example.., really need to read a
                 Scene...
        """
        pass

    def export_as_orbit(self, angle_domain, axis, prec=15):
        """
        Export object in the orbit file format
        angle_domain: sorted array of angles in radians
        axis: and array specifying the rotation axis
        """
        no_of_transforms = 1
        s = "#orbit1.n\n"
        syms = self.isometries
        no_of_syms = 0
        dir_syms = syms['direct']
        if dir_syms is not None:
            no_of_syms += len(dir_syms)
        opp_syms = syms['opposite']
        if opp_syms is not None:
            no_of_syms += len(opp_syms)
        s += "3 {} {} {} {} {}\n".format(len(self.base_shape.Vs),
                                         len(self.base_shape.Fs),
                                         no_of_syms,
                                         no_of_transforms,
                                         no_of_transforms)

        prec_str = '{{:.{}g}}'.format(prec)
        for vertex in self.base_shape.Vs:
            s += "{} {} {}\n".format(prec_str, prec_str, prec_str).format(
                vertex[0], vertex[1], vertex[2])
        for face in self.base_shape.Fs:
            line = '{}'.format(len(face))
            for i in face:
                line += ' {}'.format(i)
            line += '\n'
            s += line
        # only direct is used (includes 'opposite' as well)
        cols = self.getFaceColors()
        if self.isometries:
            if len(cols) == 1:
                col = cols[0]
                cols = [col for isom in self.isometries]
            for i, isom in enumerate(self.isometries):
                s += "c {} {} {} ".format(
                    glue.f2s(cols[i][0][0][0], prec),
                    glue.f2s(cols[i][0][0][1], prec),
                    glue.f2s(cols[i][0][0][2], prec),
                )
                s += isom.to_orbit_str(prec)
                s += '\n'
        s += "{}".format(no_of_transforms)
        for angle in angle_domain:
            s += ' {}'.format(glue.f2s(angle, prec))
        s += f"\nR _0 {glue.f2s(axis[0], prec)} {glue.f2s(axis[1], prec)} {glue.f2s(axis[2], prec)}\n"

        return s

class Scene():
    """
    Used for creating scenes in the PolyhedraBrowser.

    To implement a scene one typically needs to do the following:
    1. implement a class derived from Geom3D.SimpleShape
    2. implement a class derived from a wx.Frame window that controls the layout
       of a shape object from step 1.
    3. implement a scene class derived from this class as follows:
       class MyScene(Geom3D.Scene):
           def __init__(self, parent, canvas):
               Geom3D.Scene.__init__(self, MyShape, MyCtrlWin, parent, canvas)
       where MyShape is the class from step 1 and MyCtrlWin is the class from
       step 2.
    """
    def __init__(self, ShapeClass, CtrlWinClass, parent, canvas):
        """Create an object of the Scene class

        ShapeClass: a class derived from Geom3D.SimpleShape
        CtrlWineClass: a class derived from wx.Frame implementing controls to
                       change the properties of the shape dynamically.
        parent: the main window of the application.
        canvas: the canvas on which the shape is supposed to be drawn with
                OpenGL.
        """
        self.shape = ShapeClass()
        self.ctrlWin = CtrlWinClass(self.shape, canvas, parent, wx.ID_ANY)

    def close(self):
        try:
            self.ctrlWin.Close(True)
        except RuntimeError:
            # The user probably closed the window already
            pass


# Classes that support conversion from and to JSON:
base.class_to_json[SimpleShape] = "shape"
base.class_to_json[CompoundShape] = "compound_shape"
base.class_to_json[SymmetricShape] = "symmetric_shape"
base.class_to_json[OrbitShape] = "orbit_shape"
base.json_to_class["shape"] = CompoundShape
base.json_to_class["compound_shape"] = CompoundShape
base.json_to_class["symmetric_shape"] = SymmetricShape
base.json_to_class["orbit_shape"] = OrbitShape
