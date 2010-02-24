#!/usr/bin/python
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


import math
import rgb
import glue
import X3D
import PS
import Scenes3D
import wx
import os
from cgkit import cgtypes

from OpenGL.GLU import *
from OpenGL.GL import *

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

# Identity isometry:
E = cgtypes.quat(0, cgtypes.vec3(1, 0, 0))
# central inversion:
I = cgtypes.mat3(
        -1.0,  0.0,  0.0,
         0.0, -1.0,  0.0,
         0.0,  0.0, -1.0
    )

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

def readOffFile(fd, recreateEdges = True):
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
    i = 0
    # A dictionary where the key and value pairs are exchanged, for debugging
    # purposes:
    statesRev   = {}
    for (key, value) in states.iteritems():
        statesRev[value] = key
    state = states['checkOff']
    debug = True
    debug = False
    for line in fd:
        words = line.split()
        if len(words) > 0 and words[0][0] != '#':
            if state == states['checkOff']:
                if words[0] == 'OFF':
                    state = states['readSizes']
                else:
                    break
                if debug: print 'OFF file format recognised'
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
                if debug: print 'will read', nrOfVs, 'Vs', nrOfFs, 'Fs (', nrOfEs, 'edges)'
            elif state == states['readVs']:
                # the function assumes: no comments in beween (x, y, z) of Vs
                Vs.append(
                    cgtypes.vec3(float(words[0]), float(words[1]), float(words[2]))
                )
                if debug: print 'V[', i, '] =',  Vs[-1]
                i = i + 1
                if i == nrOfVs:
                    state = states['readFs']
                    Fs = []
                    cols = []
                    fColors = [i for i in range(nrOfFs)]
                    i = 0
            elif state == states['readFs']:
                # the function assumes: no comments in beween "q i0 .. iq-1 r g b"
                assert words[0].isdigit()
                lenF = int(words[0])
                assert (len(words) >= lenF + 4 or len(words) == lenF + 1)
                Fs.append(  [  int(words[j])     for j in range(1,      lenF+1)])
                if len(words) == lenF + 1:
                    cols.append([0.8, 0.8, 0.8])
                else:
                    cols.append(
                        [float(words[j])/255 for j in range(lenF+1, lenF+4)]
                    )
                if debug: print 'F[', i, '] =',  Fs[-1]
                if debug: print 'col[', i, '] =',  cols[-1]
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
    shape = SimpleShape(Vs, Fs, [], colors = (cols, fColors))
    if recreateEdges:
        shape.recreateEdges()
    return shape

class Fields:
    """
    This class is an empty class to be able to set some fields, like structures
    in C.
    """
    pass

class Line:
    def __init__(this, p0, p1 = None, v = None, d = 3, isSegment = False):
        """
        Define a line in a d dimensional space.

        Either specify two distinctive points p0 and p1 on the d dimensional
        line or specify a base point p0 and directional vector v. Points p0 and
        p1 should have accessable [0] .. [d-1] indices.
        """
        assert p1 == None or v == None, 'Specify either 2 points p0 and p1 or a base point p0 and a direction v!'
        this.dimension = d
        this.isSegment = isSegment
        if p1 != None:
            this.setPoints(p0, p1)
        elif v != None:
            this.setBaseDir(p0, v)

    def setPoints(this, p0, p1):
        d = [ p1[i] - p0[i] for i in range(this.dimension)]
        this.setBaseDir(p0, d)

    def setBaseDir(this, p, v):
        this.p = p
        this.v = v

    def factorInSegment(this, t, margin):
        return (
            t != None
            and
            (t >= 0 or eq(t, 0, margin))
            and
            (t <= 1 or eq(t, 1, margin))
        )

    def getPoint(this, t):
        """Returns the point on the line that equals to this.b + t*this.v (or [] when t == None)
        """
        if t != None:
            return [ this.p[i] + t * (this.v[i]) for i in range(this.dimension) ]
        else:
            return []

    def getFactorAt(this, c, i, margin = defaultFloatMargin):
        """
        Get the factor for one element constant. For an n-dimensional line it
        returns None if:
           1. the line lies in the (n-1) (hyper)plane x_i == c
           2. or the line never intersects the (n-1) (hyper)plane x_i == c.

        c: the constant
        i: index of element that should equal to c
        """
        if not eq(this.v[i], 0.0, margin):
            return (c - this.p[i]) / this.v[i]
        else:
            return None

    def vOnLine(this, v, margin = defaultFloatMargin):
        """
        Return True is V is on the line, False otherwise
        """
        t = this.getFactorAt(v[0], 0, margin)
        if t == None:
            t = this.getFactorAt(v[1], 1, margin)
        assert t != None
        return Veq(this.getPoint(t), v, margin, min(len(v), this.dimension))
        

    def getFactor(this, p, check = True, margin = defaultFloatMargin):
        """Assuming the point p lies on the line, the factor is returned.
        """
        for i in range(this.dimension):
            t =  this.getFactorAt(p[i], i, margin = margin)
            if not t == None:
                break
        assert t != None
        if check:
            c = this.getPoint(t)
            for i in range(1, this.dimension):
                if not eq(c[i], p[i], margin = margin):
                    print 'The point is not on the line; yDiff =', (c[i]-p[i])
                    assert False, 'The point is not one the line;'
        if this.isSegment:
            if not (
                (t >= 0 or eq(t, 0, margin = margin))
                and
                (t <= 1 or eq(t, 1, margin = margin))
            ):
                print 'The point is not one the line segment; t =', t
                assert False, 'The point is not one the line segment;'
        return t

class Line2D(Line):
    debug = False
    def __init__(this, p0, p1 = None, v = None, isSegment = False):
        """
        Define a line in a 2D plane.

        Either specify two distinctive points p0 and p1 on the line or specify
        a base point p0 and directional vector v. Points p0 and p1 should have
        accessable [0] and [1] indices.
        """
        Line.__init__(this, p0, p1, v, d = 2, isSegment = isSegment)

    def intersectLineGetFactor(this, l, margin = 10 * defaultFloatMargin):
        """Gets the factor for v for which the line l intersects this line

        i.e. the point of intersection is specified by this.p + restult * this.v
        If the lines are parallel, then None is returned.
        """
        nom = (l.v[0]*this.v[1]) - (l.v[1]*this.v[0])
        if not eq(nom, 0, margin):
            denom = l.v[0]*(l.p[1] - this.p[1]) + l.v[1]*(this.p[0] - l.p[0])
            return denom / nom
        else:
            return None

    def intersectLine(this, l):
        """returns the point of intersection with line l or None if the line is parallel.
        """
        return this.getPoint(this.intersectLineGetFactor(l))

    def intersectWithFacet(this, FacetVs, iFacet, z0 = 0.0, margin = defaultFloatMargin):
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
        if this.debug:
            print '-------intersectWithFacet--------'
            print 'facet indices:', iFacet
        vertexIntersections = []
        for vertexNr in range(nrOfVs):
            v0 = FacetVs[iFacet[vertexNr]]
            v1 = FacetVs[iFacet[(vertexNr + 1) % nrOfVs]]
            v0 = cgtypes.vec3(v0)
            v1 = cgtypes.vec3(v1)
            if this.debug:
                print '==> intersect line with edge nr', vertexNr, '=', v0, '->', v1
                print '(with this current line obect: {', this.p, ' + t*', this.v, ')'

            # PART 1.
            edgePV3D = Line3D(v0, v = v1-v0)
            t = edgePV3D.getFactorAt(z0, 2, margin = margin)
            s = None
            if t != None:
                tEq0 = eq(t, 0, margin)
                tEq1 = eq(t, 1, margin)
                if (t >= 0 or tEq0) and (t <= 1 or tEq1):
                    if this.debug:
                        print 'edge intersects plane z =', z0, 'in a point'
                    s = this.getFactor(edgePV3D.getPoint(t), margin = margin)
                else:
                    if this.debug:
                        print 'edge intersects plane z =', z0, 'but only if exteded (t =', t, ')'
            else:
                # Either the edge lies in the plane z = z0
                # or it is parallel with this plane
                liesInPlane = eq(v0[2], z0, margin)
                if liesInPlane:
                    if this.debug:
                        print 'edge lies in plane z =', z0
                    edgePV2D = Line2D(v0, v = v1-v0)
                    t = edgePV2D.intersectLineGetFactor(this, margin)
                    if t != None:
                        tEq0 = eq(t, 0, margin)
                        tEq1 = eq(t, 1, margin)
                        if (t >= 0 or tEq0) and (t <= 1 or tEq1):
                            s = this.intersectLineGetFactor(edgePV2D, margin)
                        else:
                            if this.debug:
                                print 'edge intersects line but only if exteded (t =', t, ')'
                    else:
                        # fix getFactor so that just getFactor is needed.
                        if this.vOnLine(v0, margin):
                            tEq0 = True
                            tEq1 = False
                            s = this.getFactor(v0, margin = margin)
                            if this.debug:
                                print 'edge is on the line'
                        else:
                            if this.debug:
                                print 'edge is parallel to the line'
                else:
                    if this.debug:
                        print 'edge parallel to plane z =', z0, '(no point of intersection)'
            if s != None:
                if this.debug:
                    print 'FOUND s = ', s, ' with v =', this.getPoint(s)
                # ie. in this case tEq0 and tEq1 should be defined
                # only add vertex intersections once (otherwise you add the
                # intersection for edge_i and edge_i+1
                if not tEq1:
                    # each item is an array that holds
                    # 0. the vertex nr
                    # 1. the index of s in pOnLineAtEdges
                    if tEq0:
                        vertexIntersections.append([vertexNr, len(pOnLineAtEdges)])
                        if this.debug:
                            print 'vertex intersection at v0'
                    pOnLineAtEdges.append(s)
                    if this.debug:
                        print 'added s = ', s
                else:
                    if this.debug:
                        print 'vertex intersection at v1, ignored'

        if this.debug:
            print 'line intersects edges (vertices) at s =', pOnLineAtEdges
            print 'vertex intersections:', vertexIntersections
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
            allOnOneLine = True
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
                    allOnOneLine = False
            if allOnOneLine:
                # see remark above for nrOfIntersectionsWithVertices == 2
                allowOddNrOfIntersections = True
            else:
                # more than 2: complex cases.
                print 'vertexIntersections', vertexIntersections
                assert False, 'ToDo'
                # if an assert is not wanted, choose pass.
                pass
        pOnLineAtEdges.sort()

#        pOnLineAtEdges.sort()
#        if this.debug: print 'pOnLineAtEdges', pOnLineAtEdges, 'before clean up'
#        for s in range(1, len(pOnLineAtEdges)):
#            if eq(pOnLineAtEdges[s-1], pOnLineAtEdges[s], margin):
#                intersectionsWithVertex.append(s)
#                if this.debug:
#                    print 'intersection with vertex:', this.getPoint(s)
#        nrOfIntersectionsWithVertices = len(intersectionsWithVertex)
#        if this.debug: print pOnLineAtEdges
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
        if this.debug: print 'pOnLineAtEdges', pOnLineAtEdges, 'after clean up'
        assert len(pOnLineAtEdges) % 2 == 0 or allowOddNrOfIntersections, "The nr of intersections should be even, are all edges unique and do they form one closed face?"
        if this.debug: print '=======intersectWithFacet========'
        return pOnLineAtEdges

class Line3D(Line):
    def __init__(this, p0, p1 = None, v = None, isSegment = False):
        """
        Define a line in 3D space.

        Either specify two distinctive points p0 and p1 on the line or specify
        a base point p0 and directional vector v. Points p0 and p1 should have
        a length of 3 and may be cgtypes.vec3.
        """
        # make sure to have cgtypes.vec3 types internally
        p0 = cgtypes.vec3(p0)
        if p1 == None:
            assert v != None
            v = cgtypes.vec3(v)
            Line.__init__(this, p0, v = v, d = 3, isSegment = isSegment)
        else:
            assert v == None
            p1 = cgtypes.vec3(p1)
            Line.__init__(this, p0, p1, d = 3, isSegment = isSegment)

    # redefine to get vec3 types:
    def setPoints(this, p0, p1):
        this.setBaseDir(p0, p1-p0)

    def getPoint(this, t):
        if t != None:
            return this.p + t * this.v
        else:
            return []

    def squareDistance2Point(this, P):
        # p81 of E.Lengyel
        q = cgtypes.vec3(P)
        hyp = q - this.p
        prjQ = hyp*this.v
        return (hyp*hyp) - ((prjQ*prjQ) / (this.v*this.v))

    def Discriminant2Line(this, L):
        # p82 of E.Lengyel
        dot = (this.v*L.v)
        return (this.v*this.v)*(L.v*L.v) - dot*dot

    def isParallel2Line(this, L):
        # p82 of E.Lengyel
        return this.Discriminant2Line(L) == 0

    def intersectWithLine(this, L, check = True, margin = defaultFloatMargin):
        D = this.Discriminant2Line(L)
        if D == 0: return None
        dx = (L.p - this.p) * this.v
        dy = (this.p - L.p) * L.v
        vpvq = this.v * L.v
        s = ((L.v * L.v) * dx +  vpvq * dy) / D
        if this.isSegment and not this.factorInSegment(s, margin):
            result = None
        else:
            result = this.getPoint(s)
            if check:
                t = (vpvq * dx + (this.v * this.v) * dy) / D
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

    def toStr(this, precision = 2):
        formatStr = "(x, y, z) = (%%0.%df, %%0.%df, %%0.%df) + t * (%%0.%df, %%0.%df, %%0.%df)" % (precision, precision, precision, precision, precision, precision)
        return formatStr % (this.p[0], this.p[1], this.p[2], this.v[0], this.v[1], this.v[2])

class Triangle:
    def __init__(this, v0, v1, v2):
        this.v = [
                cgtypes.vec3(v0[0], v0[1], v0[2]),
                cgtypes.vec3(v1[0], v1[1], v1[2]),
                cgtypes.vec3(v2[0], v2[1], v2[2])
            ]
        this.N = None

    def normal(this, normalise = False):
        if this.N == None:
            n = (this.v[1] - this.v[0]).cross(this.v[2] - this.v[0])
            if normalise:
                try: n = n.normalize()
                except ZeroDivisionError: pass
            this.N = [n[0], n[1], n[2]]
            return this.N
        else:
            return this.N

class Plane:
    """Create a plane from 3 points in the plane.

    The points should be unique.
    The plane class will contain the fields 'N' expressing the normalised norm
    and a 'D' such that for a point P in the plane 'D' = -N.P, i.e. Nx x + Ny y
    + Nz z + D = 0 is the equation of the plane.
    """
    def __init__(this, P0, P1, P2):
        assert(not P0 == P1)
        assert(not P0 == P2)
        assert(not P1 == P2)
        this.N = this.norm(P0, P1, P2)
        this.D = -this.N * cgtypes.vec3(P0)

    def norm(this, P0, P1, P2):
        """calculate the norm for the plane
        """
        v1 = cgtypes.vec3(P0) - cgtypes.vec3(P1)
        v2 = cgtypes.vec3(P0) - cgtypes.vec3(P2)
        return v1.cross(v2).normalize()

    def intersectWithPlane(this, plane, margin = defaultFloatMargin):
        """Calculates the intersections of 2 planes.

        If the planes are parallel None is returned (even if the planes define
        the same plane) otherwise a line is returned.
        """
        # See bottom of page 86 of Maths for 3D Game Programming.
        N0 = this.N
        N1 = plane.N
        if Veq(N0, N1, margin) or Veq(N0, -N1, margin):
            return None
        V = N0.cross(N1)
        M = cgtypes.mat3(N0[0], N0[1], N0[2], N1[0], N1[1], N1[2], V[0], V[1], V[2])
        Q = M.inverse() * cgtypes.vec3(-this.D, -plane.D, 0)
        return Line3D(Q, v = V)

    def toStr(this, precision = 2):
        formatStr = "%%0.%df*x + %%0.%df*y + %%0.%df*z + %%0.%df = 0)" % (precision, precision, precision, precision)
        return formatStr % (this.N[0], this.N[1], this.N[2], this.D)

def facePlane(Vs, face):
    """
    Define a Plane object from a face

    Vs: the 3D vertex coordinates
    face: the indices in Vs that form the face.
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
            #print fi_0, fi_1
            plane = Plane(
                    Vs[face[0]],
                    Vs[face[fi_0]],
                    Vs[face[fi_1]]
                )
            planeFound = True
        except ZeroDivisionError:
            fi_1 += 1
            if fi_1 >= len(face):
                fi_0 += 1
                fi_1 = fi_0 + 1
                assert fi_1 < len(face), "This face is not a face (line or point?)"
    return plane


class SimpleShape:
    dbgPrn = False
    dbgTrace = False
    className = "SimpleShape"
    bgCol     = rgb.midnightBlue[:]
    """
    This class decribes a simple 3D object consisting of faces and edges.
    """
    def __init__(this, Vs, Fs, Es = [], Ns = [], colors = ([], []), name = "SimpleShape"):
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
        colors: A tuple that definEqlHeptCanvases the colour of the faces. The tuple consists
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
        colors: A string expressing the name. This name is used e.g. when
        exporting to other formats, like PS.
        """
        if this.dbgTrace:
            print '%s.__init__(%s,..):' % (this, __class__, name)
        this.dimension = 3
        #print 'SimpleShape.Fs', Fs
        this.fNs = []
        this.generateNormals = True
        this.name = name
        this.glInitialised = False
        this.gl = Fields()
        this.gl.sphere = None
        this.gl.cyl = None
        this.gl.alwaysSetVertices = False # set to true if a scene contains more than 1 shape
        if colors[0] == []:
            colors = ([rgb.red[:]], [])
        this.scalingFactor = 1.0
        this.setVertexProperties(Vs = Vs, Ns = Ns, radius = -1., color = [1. , 1. , .8 ])
        this.setEdgeProperties(
            Es = Es, radius = -1., color = [0.1, 0.1, 0.1], drawEdges = True
        )
        this.setFaceProperties(
            Fs = Fs, colors = colors, drawFaces = True
        )
        this.defaultColor = rgb.yellow
        if this.dbgPrn:
            print '%s.__init__' % this.name
            print 'this.colorData:'
            for i in range(len(this.colorData[0])):
                print ('%d.' % i), this.colorData[0][i]
            if len(this.colorData[0]) > 1:
                assert this.colorData[0][1] != [0]
            print this.colorData[1]

    def setVertexProperties(this, dictPar = None, **kwargs):
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
        if this.dbgTrace:
            print '%s.setVertexProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Vs' in dict and dict['Vs'] != None:
                this.Vs = dict['Vs']
                this.VsRange = xrange(len(dict['Vs']))
                this.gl.updateVs = True
                this.fNsUp2date = False
            if 'Ns' in dict and dict['Ns'] != None:
                this.Ns = dict['Ns']
            if 'radius' in dict and dict['radius'] != None:
                this.gl.vRadius     = dict['radius']
                this.gl.addSphereVs = dict['radius'] > 0.0
                if this.gl.addSphereVs:
                    if this.gl.sphere != None: del this.gl.sphere
                    this.gl.sphere = Scenes3D.VSphere(radius = dict['radius'])
            if 'color' in dict and dict['color'] != None:
                this.gl.vCol = dict['color']

    def getVertexProperties(this):
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
        if this.dbgTrace:
            print '%s.getVertexProperties(%s,..):' % (this.__class__, this.name)
        return {
            'Vs': this.Vs,
            'radius': this.gl.vRadius,
            'color': this.gl.vCol,
            'Ns': this.Ns
        }

    def setEdgeProperties(this, dictPar = None, **kwargs):
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
        if this.dbgTrace:
            print '%s.setEdgeProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Es' in dict and dict['Es'] != None:
                this.Es = dict['Es']
                this.EsRange = xrange(0, len(this.Es), 2)
            if 'radius' in dict and dict['radius'] != None:
                this.gl.eRadius       = dict['radius']
                this.gl.useCylinderEs = dict['radius'] > 0.0
                if this.gl.useCylinderEs:
                    if this.gl.cyl != None: del this.gl.cyl
                    this.gl.cyl = Scenes3D.P2PCylinder(radius = dict['radius'])
            if 'color' in dict and dict['color'] != None:
                this.gl.eCol = dict['color']
            if 'drawEdges' in dict and dict['drawEdges'] != None:
                this.gl.drawEdges = dict['drawEdges']
            #print 'drawEdge:', this.gl.drawEdges, 'radius:', radius#, 'Es', this.Es

    def getEdgeProperties(this):
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
        if this.dbgTrace:
            print '%s.getEdgeProperties(%s,..):' % (this.__class__, this.name)
        return {'Es': this.Es,
                'radius': this.gl.eRadius,
                'color': this.gl.eCol,
                'drawEdges': this.gl.drawEdges
            }

    def recreateEdges(this):
        """
        Recreates the edges in the 3D object by using an adges for every side of
        a face, i.e. all faces will be surrounded by edges.

        Edges will be filtered so that shared edges between faces,
        i.e. edges that have the same vertex index, only appear once.
        The creation of edges is not optimised and can take a long time.
        """
        if this.dbgTrace:
            print '%s.recreateEdges(%s,..):' % (this.__class__, this.name)
        Es2D = []
        Es = []
        def addEdge(i, j):
            if   i < j: edge = [i, j]
            elif i > j: edge = [j, i]
            else: return
            if not edge in Es2D:
                Es2D.append(edge)
                Es.extend(edge)
        for face in this.Fs:
            lastIndex = len(face) - 1
            for i in range(lastIndex):
                addEdge(face[i], face[i+1])
            # handle the edge from the last vertex to the first vertex separately
            # (instead of using % for every index)
            addEdge(face[lastIndex], face[0])
        this.setEdgeProperties(Es = Es)

    def setFaceProperties(this, dictPar = None, **kwargs):
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
        if this.dbgTrace:
            print '%s.setFaceProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Fs' in dict and dict['Fs'] != None:
                this.setFs(dict['Fs'])
            if 'colors' in dict and dict['colors'] != None:
                this.setFaceColors(dict['colors'])
            this.divideColorWrapper()
            if 'drawFaces' in dict and dict['drawFaces'] != None:
                this.setEnableDrawFaces(dict['drawFaces'])

    def getFaceProperties(this):
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
        if this.dbgTrace:
            print '%s.getFaceProperties(%s,..):' % (this.__class__, this.name)
        return {'Fs': this.Fs,
                'colors': this.colorData,
                'drawFaces': this.gl.drawFaces
            }

    def triangulate(this, Fs):
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

    def setFs(this, Fs):
        """
        Define the shape faces

        Fs: see getFaceProperties.
        """
        if this.dbgTrace:
            print '%s.setFs(%s,..):' % (this.__class__, this.name)
        for f in Fs:
            assert (len(f) > 2), "A face should have at least 3 vertices"
        this.Fs = Fs
        this.TriangulatedFs = this.triangulate(Fs)
        #print 'Fs', Fs
        this.FsLen = len(this.Fs)
        this.FsRange = xrange(this.FsLen)
        this.fNsUp2date = False

    def setFaceColors(this, colors):
        """
        Define the colours of the faces.

        colors: see getFaceProperties.
        """
        if this.dbgTrace:
            print '%s.setFaceColors(%s,..):' % (this.__class__, this.name)
        if this.dbgPrn:
            print 'colors:', colors
        if colors[0] != None:
            colorDefs  = colors[0]
        else:
            colorDefs  = this.colorData[0]
        if colors[1] != None:
            fColors = colors[1]
        else:
            fColors = this.colorData[1]
        this.colorData = (colorDefs, fColors)
        this.nrOfColors = len(colorDefs)
        this.colRange = xrange(this.nrOfColors)
        assert(this.nrOfColors > 0), 'Empty colorDefs: %s' % colorDefs
        if this.dbgPrn:
            print '%s.setFaceColors(%s) out' % (this.__class__, this.name)
            for i in range(len(this.colorData[0])):
                print ('%d.' % i), this.colorData[0][i]
            print this.colorData[1]

    def getFaceColors(this):
        """
        Get the colours of the faces.

        Same as getFaceProperties()['colors'] but provided since setFaceColors
        exists.
        """
        if this.dbgTrace:
            print '%s.getFaceColors(%s,..):' % (this.__class__, this.name)
        return this.colorData

    def setEnableDrawFaces(this, draw = True):
        """
        Set whether the faces need to be drawn in glDraw (or not).

        draw: optional argument that is True by default. Set to False to
              disable drawing of the faces.
        """
        if this.dbgTrace:
            print '%s.setEnableDrawFaces(%s,..):' % (this.__class__, this.name)
        this.gl.drawFaces = draw

    def createFaceNormals(this, normalise):
        if not this.fNsUp2date or this.fNsNormalised != normalise:
            this.fNs = [Triangle(
                    this.Vs[f[0]], this.Vs[f[1]], this.Vs[f[2]]
                ).normal(normalise) for f in this.Fs]
            this.fNsUp2date = True
            this.fNsNormalised = normalise

    def createVertexNormals(this, normalise, Vs = None):
        if Vs == None: Vs = this.Vs
        this.createFaceNormals(normalise)
        # only use a vertex once, since the normal can be different
        this.nVs = []
        this.vNs = []
        for face, normal in zip(this.Fs, this.fNs):
            this.vNs.extend([normal for vi in face])
            this.nVs.extend([[Vs[vi][0], Vs[vi][1], Vs[vi][2]] for vi in face])
        this.createVertexNormals_vi = -1
        def inc():
            this.createVertexNormals_vi += 1
            return this.createVertexNormals_vi
        this.nFs = [[inc() for i in face] for face in this.Fs]
        this.TriangulatedFs = this.triangulate(this.nFs)
        # TODO handle the case where there are vertices in this.Vs that are not
        # indexed by this.Fs. These are lost now. You can also add an option
        # whether this should be handled.
        # I think that this might be the reason that it doesn't work so well for
        # Polychora, though it is not so important, since for Geom4D.SimpleShape
        # this will decrease performance too much anyway.
        mapVi = [-1 for v in this.Vs]
        nrOfOldVs = len(mapVi)
        this.createVertexNormals_vi = 0
        for oldFace, newFace in zip(this.Fs, this.nFs):
            for oldVi, newVi in zip(oldFace, newFace):
                if (mapVi[oldVi] == -1):
                    mapVi[oldVi] = newVi
                    if inc() >= nrOfOldVs:
                        break
            if this.createVertexNormals_vi >= nrOfOldVs: break
        this.nEs = [mapVi[oldVi] for oldVi in this.Es]

    def createDihedralAngles(this, normalise):
        None

    def divideColorWrapper(this):
        """
        Divide the specified colours over the faces. 

        This function wraps the divideColor function and handles the trivial
        cases for which there is only one colour of for which there are more
        colours than faces. These trivial cases do not need to be implemented by
        every descendent.
        """
        if this.dbgTrace:
            print '%s.divideColorWrapper(%s,..):' % (this.__class__, this.name)
        if this.dbgPrn:
            print 'this.colorData: colorDefs:'
            for i in range(len(this.colorData[0])):
                print ('%d.' % i), this.colorData[0][i]
            print 'face color indices:', this.colorData[1]
        if (len(this.colorData[1]) != this.FsLen):
            if this.nrOfColors == 1:
                this.colorData = (
                        this.colorData[0],
                        [0 for i in this.FsRange]
                    )
            elif this.nrOfColors < this.FsLen:
                this.divideColor()
            else:
                this.colorData = (
                        this.colorData[0],
                        range(this.FsLen)
                    )
            assert(len(this.colorData[1]) == this.FsLen)
        # generate an array with Equal coloured faces:
        this.EqColFs = [[] for col in range(this.nrOfColors)]
        for i in this.FsRange:
            this.EqColFs[this.colorData[1][i]].append(i)
        if this.dbgPrn:
            print '%s.divideColorWrapper(%s) out' % (this.__class__, this.name)
            print 'this.colorData: colorDefs:'
            for i in range(len(this.colorData[0])):
                print ('%d.' % i), this.colorData[0][i]
            print 'face color indices:', this.colorData[1]

    def divideColor(this):
        """
        Divide the specified colours over the isometries. 

        This function should actually be implemented by a descendent, so that
        the colours can be divided according to the symmetry. This function
        just repeats the colours until the length is long enough.
        The amount of colours should be less than the nr of isomentries.
        """
        if this.dbgTrace:
            print '%s.divideColor(%s,..):' % (this.__class__, this.name)
        div = this.FsLen / this.nrOfColors
        mod = this.FsLen % this.nrOfColors
        fColors = []
        colorIRange = range(this.nrOfColors)
        for i in range(div):
            fColors.extend(colorIRange)
        fColors.extend(range(mod))
        this.colorData = (this.colorData[0], fColors)

    def scale(this, scale):
        this.scalingFactor = scale
        this.gl.updateVs = True

    def calculateFacesG(this):
        this.fGs = [
            reduce(lambda t, i: t + this.Vs[i], f, cgtypes.vec3(0)) / len(f)
            for f in this.Fs
        ]

    def calculateSphereRadii(this, precision=12):
        """Calculate the radii for the circumscribed, inscribed and mid sphere(s)
        """
        # calculate the circumscribed spheres:
        this.spheresRadii = Fields()
        this.spheresRadii.precision = precision
        s = {}
        for v in this.Vs:
            r = round(v.length(), precision)
            try: cnt = s[r]
            except KeyError: cnt = 0
            s[r] = cnt + 1
        this.spheresRadii.circumscribed = s
        s = {}
        for i in this.EsRange:
            v = (this.Vs[this.Es[i]] +  this.Vs[this.Es[i+1]]) / 2
            r = round(v.length(), precision)
            try: cnt = s[r]
            except KeyError: cnt = 0
            s[r] = cnt + 1
        this.spheresRadii.mid = s
        s = {}
        try: G = this.fGs
        except AttributeError:
            this.calculateFacesG()
        for g in this.fGs:
            r = round(g.length(), precision)
            try: cnt = s[r]
            except KeyError: cnt = 0
            s[r] = cnt + 1
        this.spheresRadii.inscribed = s

    def glInit(this):
        """
        Initialise OpenGL for specific shapes

        Enables a derivative to use some specific OpenGL settings needed for
        this shape. This function is called in glDraw for the first time glDraw
        is called.
        """
        if this.dbgTrace:
            print '%s.glInit(%s,..):' % (this.__class__, this.name)
        glEnableClientState(GL_VERTEX_ARRAY);
        glEnableClientState(GL_NORMAL_ARRAY)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)

        this.glInitialised = True

    def glDraw(this):
        """
        Draw the base element according to the definition of the Vs, Es, Fs and
        colour settings.

        Use this.setVertexProperties(), and setEdgeProperties and
        setFaceProperties to specify how and whether to draw the vertices, edges
        and faces respectively.
        """
        if this.dbgTrace:
            print '%s.glDraw(%s,..):' % (this.__class__, this.name)
        if this.Vs == []: return
        if this.dbgPrn:
            #print this.name, "this.Vs:"
            for v in this.Vs: print v
            #print "glDraw this.Fs:", this.Fs
            #print "glDraw this.Es:", this.Es
        Es = this.Es
        if not this.glInitialised:
            this.glInit()
        # have this one here and not in glDraw, so that a client can call this
        # function as well (without having to think about this)

        if this.gl.updateVs:
            # calculate the gravitational centre. Only calculate the vertices
            # that are used:
            if eq(this.scalingFactor, 1.0):
                Vs = this.Vs
            else:
                nrUsed = glue.getVUsageIn1D(this.Vs, this.Es)
                nrUsed = glue.getVUsageIn2D(this.Vs, this.Fs, nrUsed)
                g = cgtypes.vec3(0, 0, 0)
                sum = 0
                for vIndex in this.VsRange:
                    g = g + nrUsed[vIndex] * cgtypes.vec3(this.Vs[vIndex])
                    sum = sum + nrUsed[vIndex]
                if sum != 0:
                    g = g / sum
                #print this.name, 'g:', g
                Vs = [this.scalingFactor * (cgtypes.vec3(v) - g) + g for v in this.Vs]

            # At least on Ubuntu 8.04 conversion is not needed
            # On windows and Ubuntu 9.10 the Vs cannot be an array of vec3...
            if not this.generateNormals:
                try:
                    glVertexPointerf(Vs)
                    Ns = this.Ns
                except TypeError:
                    Vs = [ [v[0], v[1], v[2]] for v in Vs ]
                    print "glDraw: converting Vs(Ns); vec3 type not accepted"
                    glVertexPointerf(Vs)
                    Ns = [ [v[0], v[1], v[2]] for v in this.Ns ]
                if Ns != []:
                    assert len(Ns) == len(Vs), 'the normal vector array Ns should have as many normals as  vertices.'
                    glNormalPointerf(Ns)
                else:
                    glNormalPointerf(Vs)
            elif this.Ns != [] and len(this.Ns) == len(Vs):
                try:
                    glVertexPointerf(Vs)
                    Ns = this.Ns
                except TypeError:
                    Vs = [ [v[0], v[1], v[2]] for v in Vs ]
                    print "glDraw: converting Vs(Ns); vec3 type not accepted"
                    glVertexPointerf(Vs)
                    Ns = [ [n[0], n[1], n[2]] for n in this.Ns ]
                glNormalPointerf(Ns)
            else:
                this.createVertexNormals(True, Vs)
                glVertexPointerf(this.nVs)
                glNormalPointerf(this.vNs)
            this.gl.updateVs = False
            this.VsSaved = Vs
        else:
            if this.gl.alwaysSetVertices:
                glVertexPointerf(this.VsSaved)
        # VERTICES
        if this.gl.addSphereVs:
            glColor(this.gl.vCol[0], this.gl.vCol[1], this.gl.vCol[2])
            for i in this.VsRange:
                this.gl.sphere.draw(this.Vs[i])
        # EDGES
        if this.gl.drawEdges:
            if this.generateNormals and (
                this.Ns == [] or len(this.Ns) != len(this.Vs)):
                Es = this.nEs
                Vs = this.nVs
            else:
                Es = this.Es
                Vs = this.Vs
            glColor(this.gl.eCol[0], this.gl.eCol[1], this.gl.eCol[2])
            if this.gl.useCylinderEs:
                # draw edges as cylinders
                #for i in range(0, len(this.Es), 2):
                for i in this.EsRange:
                    this.gl.cyl.draw(
                            v0 = Vs[Es[i]],
                            v1 = Vs[Es[i+1]]
                        )
            else:
                # draw edges as lines
                glPolygonOffset(1.0, 3.)
                glDisable(GL_POLYGON_OFFSET_FILL)
                glDrawElementsui(GL_LINES, Es)
                glEnable(GL_POLYGON_OFFSET_FILL)

        # FACES
        if this.gl.drawFaces:
            for colIndex in this.colRange:
                c = this.colorData[0][colIndex]
                if len(c) == 3:
                    glColor(c[0], c[1], c[2])
                else:
                    glColor(c[0], c[1], c[2], c[3])
                for faceIndex in this.EqColFs[colIndex]:
                    triangles = this.TriangulatedFs[faceIndex]
                    # Note triangles is a flat (ie 1D) array
                    if len(triangles) == 3:
                        glDrawElementsui(GL_TRIANGLES, triangles)
                    else:
                        # TODO: This part belongs to a GLinit:
                        glClearStencil(0)
                        stencilBits = glGetIntegerv(GL_STENCIL_BITS)
                        assert stencilBits > 0, 'Only triangle faces are supported, since there is no stencil bit'
                        # << TODO: end part that belongs to a GLinit
                        glClear(GL_STENCIL_BUFFER_BIT)
                        # use stecil buffer to triangulate.
                        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
                        glDepthMask(GL_FALSE)
                        #glDepthFunc(GL_ALWAYS)
                        # Enable Stencil, always pass test
                        glEnable(GL_STENCIL_TEST)
                        # always pass stencil test
                        glStencilFunc(GL_ALWAYS, 1, 1)
                        # stencil fail: don't care, never fails
                        # z-fail: zero
                        # both pass: invert stencil values
                        glStencilOp(GL_KEEP, GL_ZERO, GL_INVERT)
                        # Create triangulated stencil:
                        glDrawElementsui(GL_TRIANGLES, triangles)
                        # Reset colour mask and depth settings.
                        #glDepthFunc(GL_LESS)
                        if len(c) == 3:
                            glDepthMask(GL_TRUE)
                        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
                        # Draw only where stencil equals 1 (masked to 1)
                        # GL_INVERT was used, i.e. in case of e.g. 8 bits the value is
                        # either 0 or 0xff, but only the last bit is checked.
                        glStencilFunc(GL_EQUAL, 1, 1)
                        # make stencil read only:
                        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
                        # Now, write according to stencil
                        glDrawElementsui(GL_TRIANGLES, triangles)
                        if len(c) > 3:
                            glDepthMask(GL_TRUE)
                        # ready, disable stencil
                        glDisable(GL_STENCIL_TEST)

    def toX3dNode(this, id = 'SISH', precision = 5, edgeRadius = 0):
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
        if this.dbgTrace:
            print '%s.toX3dNode(%s,..):' % (this.__class__, this.name)
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
                                        for col in this.colorData[0]
                                    ]
                            ),
                        coord = X3D.Node(
                                'Coordinate',
                                DEF = vName,
                                point = [ X3D.FloatVec(v, precision)
                                        for v in this.Vs
                                    ]
                            ),
                        coordIndex = [ X3D.Index(i) for i in this.Fs],
                        colorIndex = this.colorData[1],
                        normalPerVertex = False,
                        colorPerVertex  = False,
                        ccw             = False,
                        solid           = False,
                        creaseAngle     = 0.5
                    )
                )
            ]
        if not (this.Es == []):
            if edgeRadius <= 0:
                Es = []
                for i in range(0, len(this.Es), 2):
                    Es.append([this.Es[i], this.Es[i+1]])
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
                while i < len(this.Es):
                    Es2D.append([this.Es[i], this.Es[i+1]])
                    i += 2
                shapes.append(glue.cylinderEdgesToX3d(Es2D, this.Vs, edgeRadius))
        return X3D.Node('Transform', DEF = sName, children = shapes)

    def toX3dDoc(this, id = 'SISH', precision = 5, edgeRadius = 0):
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
        if this.dbgTrace:
            print '%s.toX3dDoc(%s,..):' % (this.__class__, this.name)
        doc = X3D.Doc()
        doc.addStdMeta(this.name)
        doc.addNode(this.toX3dNode(id, precision, edgeRadius))
        return doc


    def toOffStr(this, precision=15, info = False):
        """
        Converts this SimpleShape to a string in the 3D 'off' format and returns
        the result.

        precision: The precision that will be used for printing the coordinates
                   of the vertices.
        """
        if this.dbgTrace:
            print '%s.toOffStr(%s,..):' % (this.__class__, this.name)
        #print len(this.colorData[1]), len(this.Fs)
        #for face in this.Fs:
        #    print face
        w = lambda a: '%s%s\n' % (s, a)
        s = ''
        s = w('OFF')
        s = w('#')
        s = w('# %s' % this.name)
        s = w('#')
        s = w('# file generated with python script by Marcel Tunnissen')
        if info:
            this.calculateSphereRadii()
            s = w('# inscribed sphere(s)    : %s' % str(this.spheresRadii.inscribed))
            s = w('# mid sphere(s)          : %s' % str(this.spheresRadii.mid))
            s = w('# circumscribed sphere(s): %s' % str(this.spheresRadii.circumscribed))
        s = w('# Vertices Faces Edges')
        nrOfFaces = len(this.Fs)
        nrOfEdges = len(this.Es)/2
        s = w('%d %d %d' % (len(this.Vs), nrOfFaces, nrOfEdges))
        s = w('# Vertices')
        formatStr = '%%0.%df %%0.%df %%0.%df' % (precision, precision, precision)
        for V in this.Vs:
            s = w(formatStr % (V[0], V[1], V[2]))
        s = w('# Sides and colours')
        # this.colorData[1] = [] : use this.colorData[0][0]
        # this.colorData[1] = [c0, c1, .. cn] where ci is an index i
        #                     this.colorData[0]
        #                     There should be as many colours as faces.
        if len(this.colorData[0]) == 1:
            oneColor = True
            color = this.colorData[0][0]
        else:
            oneColor = False
            assert len(this.colorData[1]) == len(this.colorData[1])
        def faceStr(face):
            s = ('%d  ' % (len(face)))
            for fi in face:
                s = ('%s%d ' % (s, fi))
            s = '%s %d %d %d' % (
                    s, color[0] * 255, color[1]*255, color[2]*255
                )
            return s
        if oneColor:
            for face in this.Fs:
                # the lambda w didn't work: (Ubuntu 9.10, python 2.5.2)
                s = '%s%s\n' % (s, faceStr(face))
        else:
            this.createFaceNormals(normalise = True)
            for i in range(nrOfFaces):
                face = this.Fs[i]
                color = this.colorData[0][this.colorData[1][i]]
                # the lambda w didn't work: (Ubuntu 9.10, python 2.5.2)
                s = '%s%s\n' % (s, faceStr(face))
                fnStr = formatStr % (
                        this.fNs[i][0], this.fNs[i][1], this.fNs[i][2]
                    )
                s = w('# face normal: %s' % fnStr)
        if info:
            for i in range(nrOfEdges):
                s = w('# edge: %d %d' % (this.Es[2*i], this.Es[2*i + 1]))
        s = w('# END')
        return s

    def toPsPiecesStr(this,
            faceIndices = [],
            scaling = 1,
            precision = 7,
            margin = 1.0e5*defaultFloatMargin,
            pageSize = PS.PageSizeA4
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
        if this.dbgTrace:
            print '%s.toPsPiecesStr(%s,..):' % (this.__class__, this.name)
        if faceIndices == []:
            faceIndices = range(len(this.Fs))
        PsDoc = PS.doc(title = this.name, pageSize = pageSize)
        offset = 0
        debug = True
        debug = False
        if debug:
            print '********toPsPiecesStr********'
            for i in range(len(this.Vs)):
                print 'V[', i, '] =', this.Vs[i]
        for i in faceIndices:
            Vs = []
            pointsIn2D = []
            Es  = []
            face = this.Fs[i]
            # find out norm
            if debug: print 'face idx:', face
            norm = facePlane(this.Vs, face).N
            if norm == None: continue # not a face.
            if debug: print 'norm before', norm
            # Find out how to rotate the faces such that the norm of the base face
            # is parallel to the z-axis to work with a 2D situation:
            # Rotate around the cross product of z-axis and norm
            # with an angle equal to the dot product of the normalised vectors.
            zAxis = cgtypes.vec3(0, 0, 1)
            to2DAngle = math.acos(zAxis * norm)
            PsPoints = []
            if not to2DAngle == 0:
                to2Daxis = norm.cross(zAxis)
                Mrot = cgtypes.quat(to2DAngle, to2Daxis).toMat3()
                # add vertices to vertex array
                for v in this.Vs:
                    Vs.append(Mrot*cgtypes.vec3(v))
                    pointsIn2D.append([Vs[-1][0], Vs[-1][1]])
                    #if debug: print 'added to Vs', Vs[-1]
            else:
                Vs = this.Vs[:]
                pointsIn2D = [[v[0], v[1]] for v in this.Vs]
            # set z-value for the z-plane, ie plane of intersection
            zBaseFace = Vs[face[0]][2]
            if debug: print 'zBaseFace =', zBaseFace
            # add edges from shares
            basePlane = facePlane(Vs, face)
            if debug: print 'basePlane', basePlane
            # split faces into
            # 1. facets that ly in the plane: baseFacets, the other facets
            #    will be intersected with these.
            # and
            # 2. facets that share one line (segment) with this plane: intersectingFacets
            #    Only save the line segment data of these.
            baseFacets = []
            Lois = []
            for intersectingFacet in this.Fs:
                if debug:
                    print 'Intersecting face[', this.Fs.index(intersectingFacet), '] =', intersectingFacet
                    print 'with face[', i, '] =', face
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
                    Loi3D = basePlane.intersectWithPlane(intersectingPlane, margin)
                if facesShareAnEdge:
                    if debug: print 'Intersecting face shares an edge'
                    pass
                elif Loi3D == None:
                    if debug: print 'No intersection for face'
                    # the face is parallel or lies in the plane
                    if zBaseFace == Vs[intersectingFacet[0]][2]:
                        # the face is lying in the plane, add to baseFacets
                        baseFacets.append(intersectingFacet)
                        # also add to PS array of lines.
                        Es.append(intersectingFacet)
                        if debug: print 'In Plane: intersectingFacet', intersectingFacet
                else: # Loi3D != None:
                    if debug:
                        if debug: print 'intersectingPlane', intersectingPlane
                        if debug: print 'Loi3D', Loi3D
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
                            intersectingFacet, Loi3D.p[2], margin)
                    if debug: print 'pInLoiFacet', pInLoiFacet
                    if pInLoiFacet != []:
                        Lois.append([loi2D, pInLoiFacet, Loi3D.p[2]])
                        if debug: Lois[-1].append(this.Fs.index(intersectingFacet))
            # for each intersecting line segment:
            for loiData in Lois:
                loi2D       = loiData[0]
                pInLoiFacet = loiData[1]
                if debug: print 'phase 2: check iFacet nr:', loiData[-1]
                # Now Intersect loi with the baseFacets.
                for baseFacet in baseFacets:
                    pInLoiBase = loi2D.intersectWithFacet(Vs, baseFacet,
                            loiData[2], margin)
                    if debug: print 'pInLoiBase', pInLoiBase
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
            PsDoc.addLineSegments(pointsIn2D, Es, scaling, precision)

        return PsDoc.toStr()

    def intersectFacets(this,
            faceIndices = [],
            margin = 1.0e5*defaultFloatMargin
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

        if this.dbgTrace:
            print '%s.intersectFacets(%s,..):' % (this.__class__, this.name)
        if faceIndices == []:
            faceIndices = range(len(this.Fs))
        debug = True
        debug = False
        if debug: print '********intersectFacets********'
        for i in faceIndices:
            # TODO: problem Vs is calculated per face...
            #       clean up later...?
            Vs = []
            pointsIn2D = []
            Es  = []
            face = this.Fs[i]
            assert len(face) > 2, 'a face should at least be a triangle'
            # find out norm
            norm = PPPnorm(
                    this.Vs[face[0]],
                    this.Vs[face[1]],
                    this.Vs[face[2]]
                )
            if debug: print 'norm before', norm
            # Find out how to rotate the faces such that the norm of the base face
            # is parallel to the z-axis to work with a 2D situation:
            # Rotate around the cross product of z-axis and norm
            # with an angle equal to the dot product of the normalised vectors.
            zAxis = cgtypes.vec3(0, 0, 1)
            to2DAngle = math.acos(zAxis * norm)
            PsPoints = []
            if to2DAngle != 0:
                to2Daxis = norm.cross(zAxis)
                Mrot = cgtypes.quat(to2DAngle, to2Daxis).toMat3()
                # add vertices to vertex array
                for v in this.Vs:
                    Vs.append(Mrot*cgtypes.vec3(v))
                    pointsIn2D.append([Vs[-1][0], Vs[-1][1]])
                    #if debug: print 'added to Vs', Vs[-1]
            else:
                Vs = this.Vs[:]
                pointsIn2D = [[v[0], v[1]] for v in this.Vs]
            # set z-value for the z-plane, ie plane of intersection
            zBaseFace = Vs[face[0]][2]
            if debug: print 'zBaseFace =', zBaseFace
            # add edges from shares
            basePlane = Plane(
                    Vs[face[0]],
                    Vs[face[1]],
                    Vs[face[2]]
                )
            if debug: print 'basePlane', basePlane
            # split faces into
            # 1. facets that ly in the plane: baseFacets, the other facets
            #    will be intersected with these.
            # and
            # 2. facets that share one line (segment) with this plane: intersectingFacets
            #    Only save the line segment data of these.
            baseFacets = []
            Lois = []
            for intersectingFacet in this.Fs:
                if debug:
                    print 'Intersecting face[', this.Fs.index(intersectingFacet), '] =', intersectingFacet
                    print 'with face[', i, '] =', face
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
                    if debug: print 'Intersecting face shares an edge'
                else:
                    Loi3D = basePlane.intersectWithPlane(intersectingPlane, margin)
                    if Loi3D == None:
                        if debug: print 'No intersection for face'
                        # the face is parallel or lies in the plane
                        if zBaseFace == Vs[intersectingFacet[0]][2]:
                            # the face is lying in the plane, add to baseFacets
                            baseFacets.append(intersectingFacet)
                            # also add to PS array of lines.
                            Es.append(intersectingFacet)
                            print 'In Plane: intersectingFacet', intersectingFacet
                    else: # Loi3D != None:
                        if debug:
                            print 'intersectingPlane', intersectingPlane
                            print 'Loi3D', Loi3D
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
                                intersectingFacet, Loi3D.p[2], margin)
                        if debug: print 'pInLoiFacet', pInLoiFacet
                        if pInLoiFacet != []:
                            Lois.append([loi2D, pInLoiFacet, Loi3D.p[2]])
                            if debug: Lois[-1].append(this.Fs.index(intersectingFacet))

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
                if debug: print 'phase 2: check iFacet nr:', loiData[-1]
                # Now Intersect loi with the baseFacets.
                for baseFacet in baseFacets:
                    pInLoiBase = loi2D.intersectWithFacet(Vs, baseFacet,
                            loiData[2], margin)
                    if debug: print 'pInLoiBase', pInLoiBase
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

    def getDome(this, level = 2):
        shape = None
        # check if level is in supported domain
        if level < 1 or level > 2: return shape
        fprop = this.getFaceProperties()
        cols = fprop['colors']
        Vs = this.Vs[:]
        nrOrgVs = len(this.Vs)
        try: G = this.fGs
        except AttributeError:
            this.calculateFacesG()
        try: outSphere = this.spheresRadii.circumscribed
        except AttributeError:
            this.calculateSphereRadii()
            outSphere = this.spheresRadii.circumscribed
        R = reduce(max, outSphere.iterkeys())
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

        for f, i in zip(this.Fs, this.FsRange):
            if level == 1:
                xFs = domiseLevel1(f, i)
                # add the gravity centres as assumed by domiseLevel1:
                addPrjVs(this.fGs)
            else:
                l = len(f)
                if l == 3:
                    xVs, xFs = domiseLevel2(f)
                    addPrjVs(xVs)
                elif l > 3:
                    tmpFs = domiseLevel1(f, i)
                    # add the gravity centres as assumed by domiseLevel1:
                    addPrjVs(this.fGs)
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

class CompoundShape(SimpleShape):
    className = "CompoundShape"
    dbgPrn = False
    dbgTrace = False
    """
    The class describes a shape that is the result of combining more than one
    SimpleShapes. The resulting shape can be treated as one, e.g. it can be
    exported as one 'OFF' file.
    """
    def __init__(this, simpleShapes, name = "CompoundShape"):
        """
        simpleShapes: an array of SimpleShape objects of which the shape is a
        compound.
        """
        if this.dbgTrace:
            print '%s.__init__(%s,..):' % (this.__class__, name)
        SimpleShape.__init__(this, [], [], name = name)
        this.setShapes(simpleShapes)

    def addShape(this, shape):
        """
        Add shape 'shape' to the current compound.
        """
        if this.dbgTrace:
            print '%s.addShape(%s,..):' % (this.__class__, this.name)
        this.shapeElements.append(shape)
        this.mergeShapes()
        
    def setShapes(this, simpleShapes):
        if this.dbgTrace:
            print '%s.setShapes(%s,..):' % (this.__class__, this.name)
        this.shapeElements = simpleShapes
        this.mergeShapes()

    def mergeShapes(this):
        """Using the current array of shapes as defined in shapeElements,
        initialise this object as a simple Shape.

        The function will create one Vs, Fs, and Es from the current definition
        of shapeElements and will initialise this object as a SimpleShape.
        """
        if this.dbgTrace:
            print '%s.mergeShapes(%s,..):' % (this.__class__, this.name)
        ss = SimpleShape([], [], name = 'simple shape for type checking')
        Vs = []
        Fs = []
        Es = []
        Ns = []
        colorDefs = []
        colorIndices = []
        for s in this.shapeElements:
            VsOffset  = len(Vs)
            colOffset = len(colorDefs)
            Vs.extend(s.Vs)
            Ns.extend(s.Ns)
            # offset all faces:
            Fs.extend([[ i+VsOffset for i in f] for f in s.Fs])
            Es.extend([ i+VsOffset for i in s.Es])
            colorDefs.extend(s.colorData[0])
            colorIndices.extend([ i+colOffset for i in s.colorData[1]])
        this.setVertexProperties(Vs = Vs, Ns = Ns)
        this.setEdgeProperties(Es = Es)
        this.setFaceProperties(Fs = Fs, colors = (colorDefs, colorIndices))
        del ss

class SymmetricShape(CompoundShape):
    dbgPrn = False
    dbgTrace = False
    className = "SymmetricShape"
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
    def __init__(this,
        Vs, Fs, Es = [], Ns = [],
        colors = [([], [])],
        directIsometries = [E], oppositeIsometry = None,
        name = "SymmetricShape"
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
                of the orbit.  The array should at least contain one tuple to
                specify the base element.
        directIsometries: the direct isometries that are needed to reproduce all
                          parts of the shape can can be transformed from the
                          specified base element through a direct isometry. 
                          See the setIsoOp and orbit functios for more info.
        oppositeIsometry: an opposite isometry that together with all the direct
                          isometries map the base element onto all elements.
                          See setIsoOp for more info.
        """
        if this.dbgTrace:
            print '%s.__init__(%s,..):' % (this.__class__, name)
        if this.dbgPrn:
            print '  directIsometries = ['
            for isom in directIsometries:
                print '    ', isom
            print '  ]'
            print '  Vs = ['
            for V in Vs:
                print '    ', V
            print '  ]'
        # this is before creating the base shape, since it check "colors"
        this.baseShape = SimpleShape(Vs, Fs, Es, Ns = Ns, colors = colors[0])
        CompoundShape.__init__(this, [this.baseShape], name = name)
        this.showBaseOnly = False
        this.setIsoOp(directIsometries, oppositeIsometry)
        this.setFaceColorsPerIsometry(colors)
        this.orbit()

    def setIsoOp(this,
        directIsometries, oppositeIsometry = None
    ):
        """
        Set the isometry operation at initialisation.

        It is recommended to set the isometry operations at initialisation
        only, otherwise you might break other properties, like the face colours.
        directIsometries: specifies an array of direct isometries. Each isometry
                          is a cgtypes.quat.
        oppositeIsometry: specifies a cgtypes.mat3 that represents an opposite
                          isometry, e.g. the central inversion or a reflection.
                          The set of opposite isometries is defined by this
                          opposite isometry applied after each direct isometry
                          in directIsometries.
                          The parameter is optional and it will be None on
                          default, meaning there will be no opposite isometries.
        As a result the client probably needs to call orbit() again.
        """
        if this.dbgTrace:
            print '%s.setIsoOp(%s,..):' % (this.__class__, this.name)
        this.isometryOperations = {
                'direct': directIsometries,
                'opposite': oppositeIsometry
            }
        assert oppositeIsometry == None or (
                isinstance(oppositeIsometry, cgtypes.mat3)
            ), 'Either oppositeIsometry should be None or it should have be of type cgtype.mat3'
        this.order = len(directIsometries)
        if oppositeIsometry != None:
            this.order = 2*this.order

    def getIsoOp(this):
        """
        Get the isometry operations.
        """
        if this.dbgTrace:
            print '%s.getIsoOp(%s,..):' % (this.__class__, this.name)
        return this.isometryOperations

    def orbit(this):
        """
        Orbit the faces according to the specified isometries

        The order of the orbit is first all direct isomtries in the order as
        specified in __init__, then all the indirect isomemetries in a similar
        order where each opposite isometry is defined as follows: I o D, 
        where 'D' is the direct isometry and 'I' is the opposite isometry.
        The result is saved in this.shapeOrbits in which each element is a
        SimpleShape. If this is not wanted anymore, use unOrbit.
        """
        if this.dbgTrace:
            print '%s.orbit(%s,..):' % (this.__class__, this.name)
        # first make sure that all isometries have a color def
        this.shapeColors = this.genColorPerShape()
        this.nrOfShapeColorDefs = len(this.shapeColors)
        assert (this.nrOfShapeColorDefs == this.order), '%d != %d' % (this.nrOfShapeColorDefs, this.order)
        # create an array of simple shapes:
        orbits = []
        i = 0
        for dirIsom in this.isometryOperations['direct']:
            MdirIsom = dirIsom.toMat3()
            Vs = [MdirIsom*cgtypes.vec3(v) for v in this.baseShape.Vs]
            Ns = [MdirIsom*cgtypes.vec3(v) for v in this.baseShape.Ns]
            orbits.append(
                SimpleShape(
                    Vs, this.baseShape.Fs, this.baseShape.Es,
                    Ns = Ns,
                    colors = this.shapeColors[i]
                )
            )
            i += 1
        MoppIsom = this.isometryOperations['opposite']
        if MoppIsom != None:
            for dirIsom in this.isometryOperations['direct']:
                MdirIsom = dirIsom.toMat3()
                Vs = [MoppIsom*MdirIsom*cgtypes.vec3(v) for v in this.baseShape.Vs]
                Ns = [MoppIsom*MdirIsom*cgtypes.vec3(v) for v in this.baseShape.Ns]
                orbits.append(
                    SimpleShape(
                        Vs, this.baseShape.Fs, this.baseShape.Es,
                        Ns = Ns,
                        colors = this.shapeColors[i]
                    )
                )
                i += 1
        this.setShapes(orbits)
        this.orbitNeeded = False

    def setFaceColorsPerIsometry(this, colors):
        """
        Define the colours of the faces per isometry.

        colors: defines the face colours, see __init__.
        As a result the client probably needs to call orbit() again.
        """
        if this.dbgTrace:
            print '%s.setFaceColorsPerIsometry(%s,..):' % (this.__class__, this.name)
        if colors == [([], [])]:
            colors = [([rgb.red[:]], [])]
        this.checkColorsPerIsometry(colors)
        this.shapeColors = colors
        this.nrOfShapeColorDefs = len(colors)
        this.orbitNeeded = True

    def checkColorsPerIsometry(this, colors):
        """
        Check some of the properties of a colors parameter (see __init__)
        """
        if this.dbgTrace:
            print '%s.checkColorsPerIsometry(%s,..):' % (this.__class__, this.name)
        if this.dbgPrn:
            print 'colors', colors
        assert len(colors) > 0, 'colors should have at least one element'
        assert len(colors[0]) == 2, 'a colors element should be a tuple of 2 elements: (colors, fColors)' 

    def genColorPerShape(this):
        """
        Divide the shape colors over the isometries and return the result.
        """
        if this.dbgTrace:
            print '%s.genColorPerShape(%s,..):' % (this.__class__, this.name)
        if this.dbgPrn:
            print 'this.shapeColors', this.shapeColors
            print 'this.nrOfShapeColorDefs =', this.nrOfShapeColorDefs, '?=', this.order, 'this.order'
        if (this.nrOfShapeColorDefs != this.order):
            if this.nrOfShapeColorDefs == 1:
                colorDataPerShape = [
                        this.shapeColors[0] for i in range(this.order)
                    ]
            elif this.nrOfShapeColorDefs < this.order:
                div = this.order / this.nrOfShapeColorDefs
                mod = this.order % this.nrOfShapeColorDefs
                colorDataPerShape = []
                for i in range(div):
                    colorDataPerShape.extend(this.shapeColors)
                colorDataPerShape.extend(this.shapeColors[:mod])
            else:
                colorDataPerShape = this.shapeColors[:this.order],
            return colorDataPerShape
        else:
            return this.shapeColors


    def setBaseVertexProperties(this, dictPar = None, **kwargs):
        """
        Set the vertices and how/whether vertices are drawn in OpenGL for the
        base element.

        Accepted are the optional (keyword) parameters:
        - Vs,
        - radius,
        - color.
        - Ns.
        Check SimpleShape.setVertexProperties for more details.
        To get correct results the client might have to call orbit() after this.
        This is not done since the client might want to set other properoties,
        e.g. for the faces / edges as well.
        """
        if this.dbgTrace:
            print '%s.setBaseVertexProperties(%s,..):' % (this.__class__, this.name)
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
                this.baseShape.setVertexProperties(Vs = Vs, Ns = Ns)
                this.orbitNeeded = True
            radius = None
            try: radius = dict['radius']
            except KeyError: pass
            color = None
            try: color = dict['color']
            except KeyError: pass
            if not (radius == None and color == None):
                this.setVertexProperties(radius = radius, color = color)

    def getBaseVertexProperties(this, dictPar = None, **kwargs):
        """
        Get the vertex properties of the base element.

        See SimpleShape.getVertexProperties for more.
        """
        return this.baseShape.getVertexProperties()

    def setBaseFaceProperties(this, dictPar = None, **kwargs):
        """
        Define the properties of the faces for the base element.

        Accepted are the optional (keyword) parameters:
          - Fs,
          - colors,
          - drawFaces.
        Check SimpleShape.setFaceProperties for more details.
        """
        if this.dbgTrace:
            print '%s.setBaseFaceProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Fs' in dict and dict['Fs'] != None:
                this.baseShape.setFaceProperties(Fs = dict['Fs'])
                this.orbitNeeded = True
            if 'colors' in dict and dict['colors'] != None:
                this.setFaceColorsPerIsometry([dict['colors']])
                # take care of by the function above:
                # this.orbitNeeded = True
            if 'drawFaces' in dict and dict['drawFaces'] != None:
                this.setEnableDrawFaces(dict['drawFaces'])

    def setBaseEdgeProperties(this, dictPar = None, **kwargs):
        """
        Specify the edges and set how they are drawn in OpenGL.

        Accepted are the optional (keyword) parameters:
          - Es,
          - radius,
          - color,
          - drawEdges.
        Check SimpleShape.setEdgeProperties for more details.
        """
        if this.dbgTrace:
            print '%s.setBaseEdgeProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Es' in dict and dict['Es'] != None:
                this.baseShape.setEdgeProperties(Es = dict['Es'])
                this.orbitNeeded = True
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
                this.setEdgeProperties(
                    radius = radius, color = color, drawEdges = drawEdges
                )

    def glDraw(this):
        if this.dbgTrace:
            print '%s.glDraw(%s,..):' % (this.__class__, this.name)
        if this.showBaseOnly:
            this.baseShape.glDraw()
        else:
            if this.orbitNeeded:
                this.orbit()
            CompoundShape.glDraw(this)

class ShapeIn4D(SimpleShape):
    Xplane  = 1
    Yplane  = 1 << 1
    Zplane  = 1 << 2
    Wplane  = 1 << 3
    planeXY = Xplane | Yplane
    planeXZ = Xplane | Zplane
    planeXW = Xplane | Wplane
    planeYZ = Yplane | Zplane
    planeYW = Yplane | Wplane
    planeZW = Zplane | Wplane

    def __init__(this, Vs, Fs, Es = [], Ns = [], colors = ([], []), name = "ShapeIn4D"):
        this.setVs(Vs)
        #print "init: this.Vs4D", this.Vs4D
        this.setProjectionProperties(11.0, 10.0)
        SimpleShape.__init__(this, this.projectTo3D_getVs(), Fs, Es, Ns, colors, name = "ShapeIn4D")
        this.VsDirty = False # expresses whether the 3D coordinates need to be updated
        this.M4 = None # expresses whether the 4D coordinates need to be updated

    def setVs(this, Vs):
        # TODO: inconsistent with SimpleShape interface.
        """
        Set the vertex array with 4 dimensional coordinates.
        """
        # make sure the vectors are cgtypes.vec4
        this.Vs4D     = [ cgtypes.vec4(v) for v in Vs ]
        this.Vs4Dorg = this.Vs4D[:]

    def setProjectionProperties(this, wCameraDistance, wProjVolume, dbg = False):
        """
        wCameraDistance: should be > 0. distance in w coordinate between the
                         camera (for which x, y, z, are 0) and the projection
                         volume>
        wProjVolume: should be >= 0. w coordinate of the near volume. This is
                     the voume in which the object is projected.
        """
        #
        #                 |
        # wCameraDistance |
        #           |     |
        #           V     |           V
        #     wC <-----> wProjV
        #                 |
        #                 |
        #                 |
        #
        assert (wProjVolume > 0)
        assert (wCameraDistance > 0)
        this.wProjVolume     = wProjVolume
        this.wCamera         = wProjVolume + wCameraDistance
        this.wCameraDistance = wCameraDistance
        this.VsDirty         = True
        if dbg:
            print "setProjectionProperties"
            print 'wCamera', this.wCamera, ' = cameraDistance + wProjectionVolumne =', wCameraDistance, '+', wProjVolume

    def projectTo3D_getVs(this):
        """
        returns an array of 3D vertices.
        """
        #print "projectTo3D_getVs"
        Vs3D = []
        for v in this.Vs4D:
            wV = v[3]
            #print "mapping v:", v
            if not eq(this.wCamera, wV):
                scale = this.wCameraDistance / (this.wCamera - wV)
                Vs3D.append([scale * v[0], scale * v[1], scale * v[2]])
                #print "new vs", Vs3D[-1]
        return Vs3D

    def projectTo3D(this):
        """
        Updates the 3D vertices.
        """
        this.setVertexProperties(Vs = this.projectTo3D_getVs())
        this.VsDirty = False

    def rotateInStdPlane(this, plane, angle, successive = False):
        """
        Rotate in a plane defined by 2 coordinate axes.

        plane: one of planeXY, planeXZ, planeXW, planeYZ, planeYW, planeZW
        angle: the angle in radials in counter-clockwise direction, while the
               planePQ has a horizontal axis P pointing to the right and a
               vertical axis Q pointing up.
        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        c =  math.cos(angle)
        s = -math.sin(angle)
        M = cgtypes.mat4(1.0)
        if   this.Xplane & plane:
            i = 0
            if   this.Yplane & plane: j = 1
            elif this.Zplane & plane: j = 2
            else                    : j = 3
        elif this.Yplane & plane:
            i = 1
            if   this.Zplane & plane: j = 2
            else                    : j = 3
        else:
            i = 2
            j = 3

        M[i, i] = c
        M[i, j] = -s
        M[j, i] = s
        M[j, j] = c
        if not successive or this.M4 == None: this.M4 = M
        else: this.M4 = M * this.M4

    def applyTransform(this, successive = False):
        """
        Apply current transformation to the original vertices.

        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        if successive:
            Vs4D = this.Vs4D
        else:
            Vs4D = this.Vs4Dorg
        for i in range(len(this.Vs4D)):
            this.Vs4D[i] = this.M4*Vs4D[i]
        this.VsDirty = True
        #try:
        #    this.onVs4DTransformed()
        #except AttributeError:
        #    pass
        this.M4 = None

    def glDraw(this):
        if this.M4 != None: this.applyTransform()
        if this.VsDirty: this.projectTo3D()
        SimpleShape.glDraw(this)

class SimpleShapeIn4D:
    dbgTrace = False
    def __init__(this, Vs, Cs, Es = [], Ns = [], colors = ([], []), name = "SimpleShapeIn4D"):
        """
        Cs: and array of cells, consisting of an array of Fs.
        """
        this.Vs4D  = [ cgtypes.vec4(v) for v in Vs ]
        this.Es    = Es
        this.Ns    = Ns
        this.name  = name
        this.cells = [
                CellIn4D(
                    Vs, Cs[i], Es, Ns,
                    colors = (colors[0], colors[1][i]),
                    name = name
                ) for i in xrange(len(Cs))
            ]
        this.setProjectionProperties(11.0, 10.0)
        this.M4               = None # expresses whether the 4D coordinates need to be updated
        this.shrinkFactor     = 1.0

# TODO: continue here: check for every func in CELL if it is needed here...
# check SimpleShape func as well?
    def setVertexProperties(this, dictPar = None, **kwargs):
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
        if this.dbgTrace:
            print 'SimpleShapeIn4D.setVertexProperties(%s,..):' % (this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            for cell in this.cells:
                cell.setVertexProperties(dict)

    def setEdgeProperties(this, dictPar = None, **kwargs):
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
        if this.dbgTrace:
            print '%s.setEdgeProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Es' in dict and dict['Es'] != None:
                dict['Es'] = []
            for cell in this.cells:
                cell.setVertexProperties(dict)

    def setFaceProperties(this, dictPar = None, **kwargs):
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
        if this.dbgTrace:
            print '%s.setFaceProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Fs' in dict and dict['Fs'] != None:
                dict['Fs'] = []
            for cell in this.cells:
                cell.setFaceProperties(dict)


    def setCellProperties(this, Cs = None, colors = None):
        """
        Define the shape faces

        Fs: see getFaceProperties.
        """
        if this.dbgTrace:
            print '%s.setCs(%s,..):' % (this.__class__, this.name)
        if Cs == None: Cs = this.Cs
        else: this.Cs = Cs
        if colors == None: colors = this.colors
        else: this.colors = colors
        assert len(Cs) == len(colors[1]), "nr of cell colours (%d) should equal nr of cells (%d)" % (len(colors[1]), len(this.cells))
        del this.cells
        this.cells = [
                CellIn4D(
                    this.Vs4D, Cs[i], this.Es, this.Ns,
                    colors = (colors[0], colors[1][i]),
                    name = this.name
                ) for i in xrange(len(Cs))
            ]

    def setProjectionProperties(this, wCameraDistance, wProjVolume, dbg = False):
        """
        wCameraDistance: should be > 0. distance in w coordinate between the
                         camera (for which x, y, z, are 0) and the projection
                         volume>
        wProjVolume: should be >= 0. w coordinate of the near volume. This is
                     the voume in which the object is projected.
        """
        #
        #                 |
        # wCameraDistance |
        #           |     |
        #           V     |           V
        #     wC <-----> wProjV
        #                 |
        #                 |
        #                 |
        #
        assert (wProjVolume > 0)
        assert (wCameraDistance > 0)
        this.wProjVolume     = wProjVolume
        this.wCamera         = wProjVolume + wCameraDistance
        this.wCameraDistance = wCameraDistance
        this.VsDirty         = True
        for cell in this.cells:
            cell.setProjectionProperties(wCameraDistance, wProjVolume, dbg)

    def rotateInStdPlane(this, plane, angle, successive = False):
        """
        Rotate in a plane defined by 2 coordinate axes.

        plane: one of D4.planeXY, D4.planeXZ, D4.planeXW, D4.planeYZ,
               D4.planeYW, D4.planeZW
        angle: the angle in radials in counter-clockwise direction, while the
               planePQ has a horizontal axis P pointing to the right and a
               vertical axis Q pointing up.
        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        c =  math.cos(angle)
        s = -math.sin(angle)
        M = cgtypes.mat4(1.0)
        if   D4.Xplane & plane:
            i = 0
            if   D4.Yplane & plane: j = 1
            elif D4.Zplane & plane: j = 2
            else                    : j = 3
        elif D4.Yplane & plane:
            i = 1
            if   D4.Zplane & plane: j = 2
            else                    : j = 3
        else:
            i = 2
            j = 3

        M[i, i] = c
        M[i, j] = -s
        M[j, i] = s
        M[j, j] = c
        if not successive or this.M4 == None: this.M4 = M
        else: this.M4 = M * this.M4

    def setShrink(this, factor):
        if this.shrinkFactor != factor:
            this.shrinkFactor = factor

    def glDraw(this):
        for cell in this.cells:
            if this.M4 != None:
                cell.setTransform(this.M4)
                cell.setShrink(this.shrinkFactor)
                # TODO: sort the cells somewhere...
                cell.glDraw()

class D4:
    Xplane  = 1
    Yplane  = 1 << 1
    Zplane  = 1 << 2
    Wplane  = 1 << 3
    planeXY = Xplane | Yplane
    planeXZ = Xplane | Zplane
    planeXW = Xplane | Wplane
    planeYZ = Yplane | Zplane
    planeYW = Yplane | Wplane
    planeZW = Zplane | Wplane

class CellIn4D(SimpleShape):
    """
    A polychoron consisting of cells
    """
    # To begin with I copied the code from ShapeIn4D. And I will change is
    # gradually. Later the code in ShapeIn4D should be removed...
    def __init__(this, Vs, Fs, Es = [], Ns = [], colors = ([], []), name = "CellIn4D"):
        """
        """
        #print "init: this.Vs4D", this.Vs4D
        this.setProjectionProperties(11.0, 10.0)
        this.shrinkFactor     = 1.0
        # TODO: what to do with Es? Ignore for now and set Es = []
        # The problem is here that Vs / Fs are filtered: Vs that are not used
        # are removed. Them Es needs to be updated, but then the interface to
        # SimpleShapeIn4D should be updated: edges need to be given per cell...
        # That is not nice....  Keep the edges on shape level instead...
        if Es != []:
            print 'CellIn4D: ignoring Es, TODO implement'
        # TODO: what to do with Ns? Ignore for now and set Ns = []
        if Ns != []:
            print 'CellIn4D: ignoring Ns, TODO implement'
        SimpleShape.__init__(this, Vs, Fs, Es, Ns, colors, name = name)
        this.VsDirty          = True # expresses whether the 3D coordinates need to be updated
        this.M4               = None # expresses whether the 4D coordinates need to be updated
        this.sortFacesUp2Date = False # expresses whether the faces are sorted from back to front (this is used for transparent faces)
        this.sortFaces        = False

    def setVertexProperties(this, dictPar = None, **kwargs):
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
        if this.dbgTrace:
            print '%s.setVertexProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            VsUpdated = 'Vs' in dict and dict['Vs'] != None
            if VsUpdated:
                this.VsRange = xrange(len(dict['Vs']))
                # make sure the vectors are cgtypes.vec4
                this.Vs4D    = [ cgtypes.vec4(v) for v in dict['Vs'] ]
                this.Vs4Dorg = this.Vs4D[:]
                this.VsDirty = True # expresses whether the 3D coordinates need to be updated
                #if not NsUpdated: 
                #    this.Ns4D = this.Ns4Dorg[:]
                del dict['Vs']
            # TODO: what to do with Ns? Ignore for now and set Ns = []
            this.Ns4D = []
            NsUpdated = 'Ns' in dict and dict['Ns'] != None
            if NsUpdated:
            #    #this.Ns4D = dict['Ns']
            #    this.Ns4D = []
            #    if not VsUpdated: 
            #        this.Vs4D = this.Vs4Dorg[:]
                del dict['Ns']
            if 'updateFs' in dict and dict['updateFs'] != None:
                this.setFs(this.FsOrg, causeVsUpdated = True)
                del dict['updateFs']
            SimpleShape.setVertexProperties(this, dict)


    def setFs(this, Fs, causeVsUpdated = False):
        """
        Define the shape faces

        Fs: see getFaceProperties.
        update: the function is called because Vs was updated.
        """
        # TODO: what to do with Ns? Ignore for now and assume Ns = []
        if this.dbgTrace:
            print '%s.setFs(%s,..):' % (this.__class__, this.name)
        if not causeVsUpdated:
            this.Vs4D = this.Vs4Dorg[:]
            this.FsOrg = [ f[:] for f in Fs ]
        SimpleShape.setFs(this, Fs)
        # remove all vertices that are not used so you only scale the vertices
        # that are used....
        glue.cleanUpVsFs(this.Vs4D, this.Fs)
        # Now add the centroids of the faces (used for sorting)
        this.faceCentroids = []
        for f in this.Fs:
            C = cgtypes.vec4([0, 0, 0, 0])
            for vIndex in f:
                C = C + this.Vs4D[vIndex]
            C = C / len(f)
            this.faceCentroids.append(C)
        # cell centroid:
        # perhaps the algorithm below is wrong. vertices that are used 2x
        # should be counted 2x in the average as well...
        # Because of the glue.cleanUp above we know that all vertices are
        # used.
        this.cellCentroid = cgtypes.vec4([0, 0, 0, 0])
        for v in this.Vs4D:
            this.cellCentroid = this.cellCentroid + v
        print 'setFs: len(this.Vs4D)', len(this.Vs4D)
        if len(this.Vs4D) == 0:
            assert len(this.Fs) == 0
        else:
            this.cellCentroid = this.cellCentroid / len(this.Vs4D)


    def setProjectionProperties(this, wCameraDistance, wProjVolume, dbg = False):
        """
        wCameraDistance: should be > 0. distance in w coordinate between the
                         camera (for which x, y, z, are 0) and the projection
                         volume>
        wProjVolume: should be >= 0. w coordinate of the near volume. This is
                     the voume in which the object is projected.
        """
        #
        #                 |
        # wCameraDistance |
        #           |     |
        #           V     |           V
        #     wC <-----> wProjV
        #                 |
        #                 |
        #                 |
        #
        assert (wProjVolume > 0)
        assert (wCameraDistance > 0)
        this.wProjVolume     = wProjVolume
        this.wCamera         = wProjVolume + wCameraDistance
        this.wCameraDistance = wCameraDistance
        this.VsDirty         = True
        if dbg:
            print "setProjectionProperties"
            print 'wCamera', this.wCamera, ' = cameraDistance + wProjectionVolumne =', wCameraDistance, '+', wProjVolume

    def projectVsTo3D(this, Vs4D):
        """
        returns an array of 3D vertices.
        """
        #print "projectTo3D_getVs"
        Vs3D = []
        for v in Vs4D:
            wV = v[3]
            #print "mapping v:", v
            if not eq(this.wCamera, wV):
                scale = this.wCameraDistance / (this.wCamera - wV)
                if eq(this.shrinkFactor, 1.0):
                    v = this.shrinkFactor * (v - this.cellCentroid) + this.cellCentroid
                scale = scale * this.shrinkFactor
                Vs3D.append([scale * v[0], scale * v[1], scale * v[2]])
                #print "new vs", Vs3D[-1]
            else:
                Vs3D.append([1e256, 1e256, 1e256])
        return Vs3D

    def projectTo3D(this):
        """
        Updates the 3D vertices.
        """
        # TODO: how to handle NS....
        this.Vs = this.projectVsTo3D(this.Vs4D)
        this.VsDirty = False
        this.gl.updateVs = True

    def rotateInStdPlane(this, plane, angle, successive = False):
        """
        Rotate in a plane defined by 2 coordinate axes.

        plane: one of D4.planeXY, D4.planeXZ, D4.planeXW, D4.planeYZ,
               D4.planeYW, D4.planeZW
        angle: the angle in radials in counter-clockwise direction, while the
               planePQ has a horizontal axis P pointing to the right and a
               vertical axis Q pointing up.
        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        c =  math.cos(angle)
        s = -math.sin(angle)
        M = cgtypes.mat4(1.0)
        if   D4.Xplane & plane:
            i = 0
            if   D4.Yplane & plane: j = 1
            elif D4.Zplane & plane: j = 2
            else                    : j = 3
        elif D4.Yplane & plane:
            i = 1
            if   D4.Zplane & plane: j = 2
            else                    : j = 3
        else:
            i = 2
            j = 3

        M[i, i] = c
        M[i, j] = -s
        M[j, i] = s
        M[j, j] = c
        if not successive or this.M4 == None: this.M4 = M
        else: this.M4 = M * this.M4

    def setTransform(this, M):
        this.M4 = M

    def applyTransform(this, successive = False):
        """
        Apply current transformation to the original vertices.

        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        if successive:
            Vs4D = this.Vs4D
        else:
            Vs4D = this.Vs4Dorg
        for i in range(len(this.Vs4D)):
            this.Vs4D[i] = this.M4*Vs4D[i]
        this.VsDirty = True
        #try:
        #    this.onVs4DTransformed()
        #except AttributeError:
        #    pass
        this.M4 = None

    def setShrink(this, factor):
        if this.shrinkFactor != factor:
            this.shrinkFactor = factor
            this.VsDirty = True

    def glDraw(this):
        resortNeeded = not this.sortFacesUp2Date
        if this.M4 != None:
            this.applyTransform()
            # makes VsDirty
        if this.VsDirty:
            this.projectTo3D()
            resortNeeded = True
        # the statement shouldn't be moved in the the above if, since only one
        # might just changed the sortFaces setting (while the Fs are not sorted)
        if resortNeeded and this.sortFaces:
            # map centroids:
            Cs3D = this.projectVsTo3D(this.faceCentroids)
            # sort on Z
            CentroidsZ = [ (Cs3D[i][2], i) for i in this.FsRange ]
            CentroidsZ.sort()
            # map faces accordingly:
            # TODO: test whether it is faster to do 1 "for C, i in CentroidsZ"
            # in which both Fs and TriangulatedFs are generated.
            this.Fs = [ this.Fs[i] for C, i in CentroidsZ ]
            this.TriangulatedFs = [ this.TriangulatedFs[i] for C, i in CentroidsZ ]
            this.sortFacesUp2Date = True
        SimpleShape.glDraw(this)

class Scene():
    """
    Used for creating scenes in the PolyhedraBrowser.

    To implement a scene one typically needs to do the following:
    1. implement a class derived from Geom3D.SimpleShape 
    2. implement a class derived from a wx.Frame window that controls the layout
       of a shape object from step 1.
    3. implement a scene class derived from this class as follows:
       class MyScene(Geom3D.Scene):
           def __init__(this, parent, canvas):
               Geom3D.Scene.__init__(this, MyShape, MyCtrlWin, parent, canvas)
       where MyShape is the class from step 1 and MyCtrlWin is the class from
       step 2.
    """
    def __init__(this, ShapeClass, CtrlWinClass, parent, canvas):
        """Create an object of the Scene class

        ShapeClass: a class derived from Geom3D.SimpleShape
        CtrlWineClass: a class derived from wx.Frame implementing controls to
                       change the properties of the shape dynamically.
        parent: the main window of the application.
        canvas: the canvas on which the shape is supposed to be drawn with
                OpenGL.
        """
        this.shape = ShapeClass()
        this.ctrlWin = CtrlWinClass(this.shape, canvas, parent, wx.ID_ANY)

    def close(this):
        try:
            this.ctrlWin.Close(True)
        except wx._core.PyDeadObjectError:
            # The user closed the window already
            pass

# Tests:
if __name__ == '__main__':

    wDir = 'tstThis'
    cwd = os.getcwd()

    if not os.path.isdir(wDir):
        os.mkdir(wDir, 0775)
    os.chdir(wDir)

    V2 = math.sqrt(2)
    Es2D = [
            [0, 1],
            [2, 3],
            [4, 5],
            [6, 7],
            [0, 2],
            [2, 4],
            [4, 6],
            [6, 0],
            [1, 3],
            [3, 5],
            [5, 7],
            [7, 1],

            [0+8, 1+8],
            [2+8, 3+8],
            [4+8, 5+8],
            [6+8, 7+8],
            [0+8, 2+8],
            [2+8, 4+8],
            [4+8, 6+8],
            [6+8, 0+8],
            [1+8, 3+8],
            [3+8, 5+8],
            [5+8, 7+8],
            [7+8, 1+8],

            [0+16, 1+16],
            [2+16, 3+16],
            [4+16, 5+16],
            [6+16, 7+16],
            [0+16, 2+16],
            [2+16, 4+16],
            [4+16, 6+16],
            [6+16, 0+16],
            [1+16, 3+16],
            [3+16, 5+16],
            [5+16, 7+16],
            [7+16, 1+16],
        ]
    Es = []
    for e in Es2D:
        Es.extend(e)
    class ClassicCompoundOf3Cubes(SimpleShape):
        """A simple shape representing a classic compound of 3 cubes.
        """
        def __init__(this, cols):
            qCol = len(cols)
            if qCol == 3:
                fColors = [
                        0, 0, 0, 0, 0, 0,
                        1, 1, 1, 1, 1, 1,
                        2, 2, 2, 2, 2, 2,
                    ]
            elif qCol == 1:
                fColors = [0 for i in range(18)]
            elif qCol == 8:
                fColors = [i for i in range(18)]
            else:
                assert False, "Cannot handle this nr of colours"
            SimpleShape.__init__(this,
                    Vs = [
                        cgtypes.vec3(V2, 0, 1),
                        cgtypes.vec3(V2, 0, -1),
                        cgtypes.vec3(0, V2, 1),
                        cgtypes.vec3(0, V2, -1),
                        cgtypes.vec3(-V2, 0, 1),
                        cgtypes.vec3(-V2, 0, -1),
                        cgtypes.vec3(0, -V2, 1),
                        cgtypes.vec3(0, -V2, -1),

                        cgtypes.vec3(0, 1, V2),
                        cgtypes.vec3(0, -1, V2),
                        cgtypes.vec3(V2, 1, 0),
                        cgtypes.vec3(V2, -1, 0),
                        cgtypes.vec3(0, 1, -V2),
                        cgtypes.vec3(0, -1, -V2),
                        cgtypes.vec3(-V2, 1, 0),
                        cgtypes.vec3(-V2, -1, 0),

                        cgtypes.vec3(1, 0, V2),
                        cgtypes.vec3(-1, 0, V2),
                        cgtypes.vec3(1, -V2, 0),
                        cgtypes.vec3(-1, -V2, 0),
                        cgtypes.vec3(1, 0, -V2),
                        cgtypes.vec3(-1, 0, -V2),
                        cgtypes.vec3(1, V2, 0),
                        cgtypes.vec3(-1, V2, 0)
                    ],
                    Fs = [
                            [0, 1, 3, 2],     # 0
                            [2, 3, 5, 4],     # 1
                            [4, 5, 7, 6],     # 2
                            [6, 7, 1, 0],     # 3
                            [0, 2, 4, 6],     # 4
                            [7, 5, 3, 1],     # 5

                            [0+8, 1+8, 3+8, 2+8],     # 6
                            [2+8, 3+8, 5+8, 4+8],     # 7
                            [4+8, 5+8, 7+8, 6+8],     # 8
                            [6+8, 7+8, 1+8, 0+8],     # 9
                            [0+8, 2+8, 4+8, 6+8],     # 10
                            [7+8, 5+8, 3+8, 1+8],     # 11

                            [0+16, 1+16, 3+16, 2+16],     # 12
                            [2+16, 3+16, 5+16, 4+16],     # 13
                            [4+16, 5+16, 7+16, 6+16],     # 14
                            [6+16, 7+16, 1+16, 0+16],     # 15
                            [0+16, 2+16, 4+16, 6+16],     # 16
                            [7+16, 5+16, 3+16, 1+16]      # 17
                        ],
                    Es = Es,
                    colors = (cols, fColors)
                )

    cc = ClassicCompoundOf3Cubes([rgb.red, rgb.yellow, rgb.blue])
    fd = open('classicCompound3Cubes.off', 'w')
    fd.write(cc.toOffStr())
    del fd

    fd = open('classicCompound3Cubes.wrl', 'w')
    x3d = cc.toX3dDoc(edgeRadius = 0.03)
    x3d.setFormat(X3D.VRML_FMT)
    fd.write(x3d.toStr())
    del fd

    fd = open('classicCompound3Cubes.x3d', 'w')
    x3d.setFormat(X3D.X3D_FMT)
    fd.write(x3d.toStr())
    del fd
    del x3d
    if True:
        fd = open('classicCompound3Cubes.ps', 'w')
        #cc.Fs = [cc.Fs[4], cc.Fs[9], cc.Fs[10]]
        #fd.write(cc.toPsPiecesStr(faceIndices = [0], scaling = 100))
        fd.write(cc.toPsPiecesStr(faceIndices = [0, 4], scaling = 100))
        del fd
    del cc

    import wx

    cubeVs = [
            cgtypes.vec3(V2, 0, 1),
            cgtypes.vec3(V2, 0, -1),
            cgtypes.vec3(0, V2, 1),
            cgtypes.vec3(0, V2, -1),
            cgtypes.vec3(-V2, 0, 1),
            cgtypes.vec3(-V2, 0, -1),
            cgtypes.vec3(0, -V2, 1),
            cgtypes.vec3(0, -V2, -1),
        ]
    cubeFs = [
            [0, 1, 3, 2],     # 0
            [2, 3, 5, 4],     # 1
            [4, 5, 7, 6],     # 2
            [6, 7, 1, 0],     # 3
            [0, 2, 4, 6],     # 4
            [7, 5, 3, 1],     # 5
        ]
    cubeEs = [
            0, 1, 2, 3, 4, 5, 6, 7,
            0, 2, 2, 4, 4, 6, 6, 0,
            1, 3, 3, 5, 5, 7, 7, 1,
        ]
    simpleCube = SimpleShape(
        Vs = cubeVs,
        Fs = cubeFs,
        Es = cubeEs,
        colors = ([rgb.red], [0]),
    )
    cubes3 = SymmetricShape(
        Vs = cubeVs,
        Fs = cubeFs,
        Es = cubeEs,
        colors = [
                ([rgb.red],    [0]),
                ([rgb.yellow], [0]),
                ([rgb.blue],   [0]),
            ],
        directIsometries = [
                E,
                cgtypes.quat(math.pi/2, cgtypes.vec3(1, 0, 0)),
                cgtypes.quat(math.pi/2, cgtypes.vec3(0, 1, 0))
            ]
    )
    class TestCanvas(Scenes3D.Interactive3DCanvas):
        def __init__(this, shape, *args, **kwargs):
            this.shape = shape
            Scenes3D.Interactive3DCanvas.__init__(this, *args, **kwargs)

        def initGl(this):
            glMatrixMode(GL_PROJECTION)
            gluPerspective(45., 1.0, 1., 300.)
            #TODO: Render_cameraTransform(rctx)

            glMatrixMode(GL_MODELVIEW)
            glTranslatef(0.0, 0.0, -15.0)
            
            #glShadeModel(GL_SMOOTH)

            glEnableClientState(GL_VERTEX_ARRAY);
            glEnableClientState(GL_NORMAL_ARRAY)

            #glLightfv(GL_LIGHT0, GL_POSITION, this.lightPosition)
            #glLightfv(GL_LIGHT0, GL_AMBIENT, this.lightAmbient)
            #glLightfv(GL_LIGHT0, GL_DIFFUSE, this.lightDiffuse)
            #glLightfv(GL_LIGHT0, GL_SPECULAR, this.lightDiffuse)
            #glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, this.materialSpec)
            glEnable(GL_LIGHT0)

            glEnable(GL_COLOR_MATERIAL)
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_NORMALIZE)
            glClearColor(this.bgCol[0], this.bgCol[1], this.bgCol[2], 0)

        def onPaint(this):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            this.shape.glDraw()

    class TestWindow(wx.Frame):
        def __init__(this, TstScene, shape, *args, **kwargs):
            wx.Frame.__init__(this, *args, **kwargs)
            this.addMenuBar()
            this.statusBar = this.CreateStatusBar()
            this.panel = TestPanel(this, TstScene, shape, wx.ID_ANY)
            this.Show(True)
            this.Bind(wx.EVT_CLOSE, this.onClose)
            this.exportDirName = '.'
            this.importDirName = '.'
            this.viewSettingsWindow = None

        def addMenuBar(this):
            menuBar = wx.MenuBar()
            menuBar.Append(this.createFileMenu(), '&File')
            menuBar.Append(this.createEditMenu(), '&Edit')
            this.SetMenuBar(menuBar)

        def createFileMenu(this):
            menu = wx.Menu()
            open = wx.MenuItem(
                    menu,
                    wx.ID_ANY,
                    text = "&Open\tCtrl+O"
                )
            this.Bind(wx.EVT_MENU, this.onOpen, id = open.GetId())
            menu.AppendItem(open)
            add = wx.MenuItem(
                    menu,
                    wx.ID_ANY,
                    text = "&Add\tCtrl+A"
                )
            this.Bind(wx.EVT_MENU, this.onAdd, id = add.GetId())
            menu.AppendItem(add)
            export = wx.Menu()
            saveAsOff = wx.MenuItem(
                    menu,
                    wx.ID_ANY,
                    text = "&Off\tCtrl+E"
                )
            this.Bind(wx.EVT_MENU, this.onSaveAsOff, id = saveAsOff.GetId())
            export.AppendItem(saveAsOff)
            saveAsPs = wx.MenuItem(
                    menu,
                    wx.ID_ANY,
                    text = "&PS\tCtrl+P"
                )
            this.Bind(wx.EVT_MENU, this.onSaveAsPs, id = saveAsPs.GetId())
            export.AppendItem(saveAsPs)
            menu.AppendMenu(wx.ID_ANY, "&Export", export)
            menu.AppendSeparator()
            exit = wx.MenuItem(
                    menu,
                    wx.ID_ANY,
                    text = "E&xit\tCtrl+X"
                )
            this.Bind(wx.EVT_MENU, this.onExit, id = exit.GetId())
            menu.AppendItem(exit)
            return menu

        def createEditMenu(this):
            menu = wx.Menu()
            viewSettings = wx.MenuItem(
                    menu,
                    wx.ID_ANY,
                    text = "&View Settings\tCtrl+W"
                )
            this.Bind(wx.EVT_MENU, this.onViewSettings, id = viewSettings.GetId())
            menu.AppendItem(viewSettings)
            return menu

        def onOpen(this, e):
            dlg = wx.FileDialog(this, 'New: Choose a file', this.importDirName, '', '*.*off', wx.OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                this.filename = dlg.GetFilename()
                this.importDirName  = dlg.GetDirectory()
                fd = open(os.path.join(this.importDirName, this.filename), 'r')
                # Create a compound shape to be able to add shapes later.
                newShape = CompoundShape([readOffFile(fd, recreateEdges = True)])
                this.panel.setShape(newShape)
                fd.close()
                this.SetTitle('%s (%s)' % (this.filename, this.importDirName))
            dlg.Destroy()

        def onAdd(this, e):
            dlg = wx.FileDialog(this, 'Add: Choose a file', this.importDirName, '', '*.*off', wx.OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                this.filename = dlg.GetFilename()
                this.importDirName  = dlg.GetDirectory()
                fd = open(os.path.join(this.importDirName, this.filename), 'r')
                # Create a compound shape to be able to add shapes later.
                this.panel.getShape().addShape(readOffFile(fd, recreateEdges = True))
                fd.close()
                # TODO: set better title
                this.SetTitle('Added: %s (%s)' % (this.filename, this.importDirName))
            dlg.Destroy()

        def onSaveAsOff(this, e):
            dlg = wx.FileDialog(this, 'Save as .off file', this.exportDirName, '', '*.off', wx.SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                this.filename = dlg.GetFilename()
                this.exportDirName  = dlg.GetDirectory()
                NameExt = this.filename.split('.')
                if len(NameExt) == 1:
                    this.filename = '%s.off' % this.filename
                elif NameExt[-1].lower() != 'off':
                    if NameExt[-1] != '':
                        this.filename = '%s.off' % this.filename
                    else:
                        this.filename = '%soff' % this.filename
                # TODO: check if file exists... do not overwrite on default
                fd = open(os.path.join(this.exportDirName, this.filename), 'w')
                # TODO precision through setting:
                fd.write(this.panel.getShape().toOffStr())
                fd.close()
                this.SetTitle('%s (%s)' % (this.filename, this.exportDirName))
            dlg.Destroy()

        def onSaveAsPs(this, e):
            dlg = wx.FileDialog(this, 'Save as .off file', this.exportDirName, '', '*.ps', wx.SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                this.filename = dlg.GetFilename()
                this.exportDirName  = dlg.GetDirectory()
                NameExt = this.filename.split('.')
                if len(NameExt) == 1:
                    this.filename = '%s.ps' % this.filename
                elif NameExt[-1].lower() != 'ps':
                    if NameExt[-1] != '':
                        this.filename = '%s.ps' % this.filename
                    else:
                        this.filename = '%sps' % this.filename
                # TODO: check if file exists... do not overwrite on default
                fd = open(os.path.join(this.exportDirName, this.filename), 'w')
                # TODO precision through setting:
                # TODO scalingSize through setting:
                # TODO faceIndices through setting:
                fd.write(this.panel.getShape().toPsPiecesStr())
                fd.close()
                this.SetTitle('%s (%s)' % (this.filename, this.exportDirName))
            dlg.Destroy()

        def onViewSettings(this, e):
            if this.viewSettingsWindow == None:
                this.viewSettingsWindow = ViewSettingsWindow(this.panel.getCanvas(),
                    None, wx.ID_ANY,
                    title = 'View Settings',
                    size = (394, 300)
                )
                this.viewSettingsWindow.Bind(wx.EVT_CLOSE, this.onViewSettingsClose)
            else:
                this.viewSettingsWindow.SetFocus()
                this.viewSettingsWindow.Raise()

        def setStatusStr(this, str):
            this.statusBar.SetStatusText(str)

        def onExit(this, e):
            this.Close(True)

        def onViewSettingsClose(this, event):
            this.viewSettingsWindow.Destroy()
            this.viewSettingsWindow = None

        def onClose(this, event):
            print 'main onclose'
            this.Destroy()
            if this.viewSettingsWindow != None:
                this.viewSettingsWindow.Close()

    class TestPanel(wx.Panel):
        def __init__(this, parent, TstScene, shape, *args, **kwargs):
            wx.Panel.__init__(this, parent, *args, **kwargs)
            this.parent = parent
            # Note that uncommenting this will override the default size
            # handler, which resizes the sizers that are part of the Frame.
            #this.Bind(wx.EVT_SIZE, this.onSize)

            this.canvas = TstScene(shape, this)
            this.canvas.SetMinSize((300, 300))
            this.canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
            this.canvasSizer.Add(this.canvas)

            # Ctrl Panel:
            #this.ctrlSizer = ViewSettingsSizer(parent, this, this.canvas)
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.Add(this.canvas, 3, wx.EXPAND)
            #mainSizer.Add(this.ctrlSizer, 2, wx.EXPAND)
            this.SetSizer(mainSizer)
            this.SetAutoLayout(True)
            this.Layout()

        def getCanvas(this):
            return this.canvas

        def onSize(this, event):
            """Print the size plus an offset for y that includes the title bar.

            This function is used to set the ctrl window size in the interactively.
            Bind this function, and read and set the correct size in the scene.
            """
            s = this.GetClientSize()
            print 'Window size:', (s[0]+2, s[1]+54)
            this.Layout()

        def setShape(this, shape):
            """Set a new shape to be shown with the current viewing settings

            shape: the new shape.
            """
            oldShape = this.canvas.shape
            this.canvas.shape = shape
            # Use all the vertex settings except for Vs, i.e. keep the view
            # vertex settings the same.
            oldVSettings = oldShape.getVertexProperties()
            del oldVSettings['Vs']
            this.canvas.shape.setVertexProperties(oldVSettings)
            # Use all the edge settings except for Es
            oldESettings = oldShape.getEdgeProperties()
            del oldESettings['Es']
            this.canvas.shape.setEdgeProperties(oldESettings)
            # Use only the 'drawFaces' setting:
            oldFSettings = {
                    'drawFaces': oldShape.getFaceProperties()['drawFaces']
                }
            this.canvas.shape.setFaceProperties(oldFSettings)
            this.canvas.paint()
            del oldShape

        def getShape(this):
            """Return the current shape object
            """
            return this.canvas.shape

    class ViewSettingsWindow(wx.Frame):
        def __init__(this, canvas, *args, **kwargs):
            wx.Frame.__init__(this, *args, **kwargs)
            this.canvas    = canvas
            this.statusBar = this.CreateStatusBar()
            this.panel     = wx.Panel(this, wx.ID_ANY)
            this.ctrlSizer = ViewSettingsSizer(this, this.panel, this.canvas)
            this.panel.SetMinSize((300, 240))
            this.panel.SetSizer(this.ctrlSizer)
            this.panel.SetAutoLayout(True)
            this.panel.Layout()
            this.Show(True)

        def setStatusStr(this, str):
            this.statusBar.SetStatusText(str)

    class ViewSettingsSizer(wx.BoxSizer):
        def __init__(this, parentWindow, parentPanel, canvas, *args, **kwargs):
            """
            Create a sizer with view settings.

            parentWindow: the parentWindow object. This is used to update de
                          status string in the status bar. The parent window is
                          supposed to contain a function setStatusStr for this
                          to work.
            parentPanel: The panel to add all control widgets to.
            canvas: 
            canvas: An interactive 3D canvas object. This object is supposed to
                    have a shape field that points to the shape object that is
                    being viewed.
            """

            wx.BoxSizer.__init__(this, wx.VERTICAL, *args, **kwargs)
            this.canvas       = canvas
            this.parentWindow = parentWindow
            this.parentPanel  = parentPanel
            # Show / Hide vertices
            vProps            = canvas.shape.getVertexProperties()
            this.vR           = vProps['radius']
            this.vOptionsLst  = ['hide', 'show']
            if this.vR > 0:
                default = 1 # key(1) = 'show'
            else:
                default = 0 # key(0) = 'hide'
            this.vOptionsGui  = wx.RadioBox(this.parentPanel,
                label = 'Vertex Options',
                style = wx.RA_VERTICAL,
                choices = this.vOptionsLst
            )
            this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onVOption, id = this.vOptionsGui.GetId())
            this.vOptionsGui.SetSelection(default)
            # Vertex Radius
            nrOfSliderSteps   = 40
            this.vRadiusMin   = 0.01 
            this.vRadiusMax   = 0.100
            this.vRadiusScale = 1.0 / this.vRadiusMin
            s = (this.vRadiusMax - this.vRadiusMin) * this.vRadiusScale
            if int(s) < nrOfSliderSteps:
                this.vRadiusScale = (this.vRadiusScale * nrOfSliderSteps) / s
            this.vRadiusGui = wx.Slider(this.parentPanel,
                value = this.vRadiusScale * this.vR,
                minValue = this.vRadiusScale * this.vRadiusMin,
                maxValue = this.vRadiusScale * this.vRadiusMax,
                style = wx.SL_HORIZONTAL
            )
            this.parentPanel.Bind(wx.EVT_SLIDER, this.onVRadius, id = this.vRadiusGui.GetId())
            this.vRadiusBox = wx.StaticBox(this.parentPanel, label = 'Vertex radius')
            # disable if vertices are hidden anyway:
            if default != 1: 
                this.vRadiusGui.Disable()
            # Vertex Colour
            this.vColorGui = wx.Button(this.parentPanel, wx.ID_ANY, "Colour")
            this.parentPanel.Bind(wx.EVT_BUTTON, this.onVColor, id = this.vColorGui.GetId())
            # Show / hide edges
            eProps           = canvas.shape.getEdgeProperties()
            this.eR          = eProps['radius']
            this.eOptionsLst = ['hide', 'as cylinders', 'as lines']
            if eProps['drawEdges']:
                if this.vR > 0:
                    default = 1 # key(1) = 'as cylinders'
                else:
                    default = 2 # key(2) = 'as lines'
            else:
                default     = 0 # key(0) = 'hide'
            this.eOptionsGui = wx.RadioBox(this.parentPanel,
                label = 'Edge Options',
                style = wx.RA_VERTICAL,
                choices = this.eOptionsLst
            )
            this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onEOption, id = this.eOptionsGui.GetId())
            this.eOptionsGui.SetSelection(default)
            # Edge Radius
            nrOfSliderSteps   = 40
            this.eRadiusMin   = 0.008 
            this.eRadiusMax   = 0.08
            this.eRadiusScale = 1.0 / this.eRadiusMin
            s = (this.eRadiusMax - this.eRadiusMin) * this.eRadiusScale
            if int(s) < nrOfSliderSteps:
                this.eRadiusScale = (this.eRadiusScale * nrOfSliderSteps) / s
            this.eRadiusGui = wx.Slider(this.parentPanel,
                value = this.eRadiusScale * this.eR,
                minValue = this.eRadiusScale * this.eRadiusMin,
                maxValue = this.eRadiusScale * this.eRadiusMax,
                style = wx.SL_HORIZONTAL
            )
            this.parentPanel.Bind(wx.EVT_SLIDER, this.onERadius, id = this.eRadiusGui.GetId())
            this.eRadiusBox = wx.StaticBox(this.parentPanel, label = 'Edge radius')
            # disable if edges are not drawn as scalable items anyway:
            if default != 1: 
                this.eRadiusGui.Disable()
            # Edge Colour
            this.eColorGui = wx.Button(this.parentPanel, wx.ID_ANY, "Colour")
            this.parentPanel.Bind(wx.EVT_BUTTON, this.onEColor, id = this.eColorGui.GetId())
            # Show / hide face
            default = 1
            this.fOptionsLst = ['hide', 'show']
            this.fOptionsGui = wx.RadioBox(this.parentPanel,
                label = 'Face Options',
                style = wx.RA_VERTICAL,
                choices = this.fOptionsLst
            )
            this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onFOption, id = this.fOptionsGui.GetId())
            this.fOptionsGui.SetSelection(default)
            # Sizers
            vRadiusSizer = wx.StaticBoxSizer(this.vRadiusBox, wx.VERTICAL)
            vRadiusSizer.Add(this.vRadiusGui, 1, wx.EXPAND | wx.TOP    | wx.LEFT)
            vRadiusSizer.Add(this.vColorGui,  1,             wx.BOTTOM | wx.LEFT)
            eRadiusSizer = wx.StaticBoxSizer(this.eRadiusBox, wx.VERTICAL)
            eRadiusSizer.Add(this.eRadiusGui, 1, wx.EXPAND | wx.TOP    | wx.LEFT)
            eRadiusSizer.Add(this.eColorGui,  1,             wx.BOTTOM | wx.LEFT)
            #sizer = wx.BoxSizer(wx.VERTICAL)
            vSizer = wx.BoxSizer(wx.HORIZONTAL)
            vSizer.Add(this.vOptionsGui, 2, wx.EXPAND)
            vSizer.Add(vRadiusSizer, 5, wx.EXPAND)
            eSizer = wx.BoxSizer(wx.HORIZONTAL)
            eSizer.Add(this.eOptionsGui, 2, wx.EXPAND)
            eSizer.Add(eRadiusSizer, 5, wx.EXPAND)
            this.Add(vSizer, 5, wx.EXPAND)
            this.Add(eSizer, 5, wx.EXPAND)
            this.Add(this.fOptionsGui, 4, wx.EXPAND)
            this.setStatusStr()

        def setStatusStr(this):
            try:
                this.parentWindow.setStatusStr('V-Radius: %0.5f; E-Radius: %0.5f' % (this.vR, this.eR))
            except AttributeError:
                print "parentWindow.setStatusStr function undefined"

        def onVOption(this, e):
            #print 'onVOption'
            sel = this.vOptionsGui.GetSelection()
            selStr = this.vOptionsLst[sel]
            if selStr == 'show':
                this.vRadiusGui.Enable()
                this.canvas.shape.setVertexProperties(radius = this.vR)
            elif selStr == 'hide':
                this.vRadiusGui.Disable()
                this.canvas.shape.setVertexProperties(radius = -1.0)
            this.canvas.paint()

        def onVRadius(this, e):
            this.vR = (float(this.vRadiusGui.GetValue()) / this.vRadiusScale)
            this.canvas.shape.setVertexProperties(radius = this.vR)
            this.canvas.paint()
            this.setStatusStr()

        def onVColor(this, e):
            dlg = wx.ColourDialog(this.parentWindow)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                rgba = data.GetColour()
                rgb  = rgba.Get()
                this.canvas.shape.setVertexProperties(
                    color = [float(i)/256 for i in rgb]
                )
                this.canvas.paint()
            dlg.Destroy()

        def onEOption(this, e):
            sel = this.eOptionsGui.GetSelection()
            selStr = this.eOptionsLst[sel]
            if selStr == 'hide':
                this.eRadiusGui.Disable()
                this.canvas.shape.setEdgeProperties(drawEdges = False)
            elif selStr == 'as cylinders':
                this.eRadiusGui.Enable()
                this.canvas.shape.setEdgeProperties(drawEdges = True)
                this.canvas.shape.setEdgeProperties(radius = this.eR)
            elif selStr == 'as lines':
                this.eRadiusGui.Disable()
                this.canvas.shape.setEdgeProperties(drawEdges = True)
                this.canvas.shape.setEdgeProperties(radius = 0)
            this.canvas.paint()

        def onERadius(this, e):
            this.eR = (float(this.eRadiusGui.GetValue()) / this.eRadiusScale)
            this.canvas.shape.setEdgeProperties(radius = this.eR)
            this.canvas.paint()
            this.setStatusStr()

        def onEColor(this, e):
            dlg = wx.ColourDialog(this.parentWindow)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                rgba = data.GetColour()
                rgb  = rgba.Get()
                this.canvas.shape.setEdgeProperties(
                    color = [float(i)/256 for i in rgb]
                )
                this.canvas.paint()
            dlg.Destroy()

        def onFOption(this, e):
            sel = this.fOptionsGui.GetSelection()
            selStr = this.fOptionsLst[sel]
            this.canvas.shape.setFaceProperties(drawFaces = (selStr == 'show'))
            this.canvas.paint()

    app = wx.PySimpleApp()
    frame = TestWindow(
            TestCanvas,
            #ClassicCompoundOf3Cubes([rgb.red, rgb.yellow, rgb.blue]),
            #simpleCube,
            cubes3,
            None, wx.ID_ANY, "test",
            size = (430, 482),
            pos = wx.Point(980, 0)
        )
    app.MainLoop()
