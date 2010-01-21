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
import Geom3D
import wx
from cgkit import cgtypes
from copy import copy

from OpenGL.GLU import *
from OpenGL.GL import *

class Axis:
    X  = 1
    Y  = 1 << 1
    Z  = 1 << 2
    W  = 1 << 3

class Plane:
    XY = Axis.X | Axis.Y
    XZ = Axis.X | Axis.Z
    XW = Axis.X | Axis.W
    YZ = Axis.Y | Axis.Z
    YW = Axis.Y | Axis.W
    ZW = Axis.Z | Axis.W

class vec(cgtypes.vec4):

    orthogonalMargin = 1.0e-6
    def __init__(this, *args):
        cgtypes.vec4.__init__(this, *args)

    def isParallel(this, v, margin = Geom3D.defaultFloatMargin):
        z0 = z1 = z2 = z3 = False # expresses whether this[i] == v[i] == 0
        q0, q1, q2, q3 = 1, 2, 3, 4 # initialise all differently
        try:
            q0 = this.x/v.x
        except ZeroDivisionError:
            z0 = Geom3D.eq(this.x, 0.0, margin)
        try:
            q1 = this.y/v.y
        except ZeroDivisionError:
            z1 = Geom3D.eq(this.y, 0.0, margin)
        try:
            q2 = this.z/v.z
        except ZeroDivisionError:
            z2 = Geom3D.eq(this.z, 0.0, margin)
        try:
            q3 = this.w/v.w
        except ZeroDivisionError:
            z3 = Geom3D.eq(this.w, 0.0, margin)
        if (not z0):
            return (
                    (z1 or Geom3D.eq(q0, q1, margin))
                    and
                    (z2 or Geom3D.eq(q0, q2, margin))
                    and
                    (z3 or Geom3D.eq(q0, q3, margin))
                )
        elif (not z1):
            return (
                    (z0 or Geom3D.eq(q1, q0, margin))
                    and
                    (z2 or Geom3D.eq(q1, q2, margin))
                    and
                    (z3 or Geom3D.eq(q1, q3, margin))
                )
        elif (not z2):
            return (
                    (z0 or Geom3D.eq(q2, q0, margin))
                    and
                    (z1 or Geom3D.eq(q2, q1, margin))
                    and
                    (z3 or Geom3D.eq(q2, q3, margin))
                )
        elif (not z3):
            return (
                    (z0 or Geom3D.eq(q3, q0, margin))
                    and
                    (z1 or Geom3D.eq(q3, q1, margin))
                    and
                    (z2 or Geom3D.eq(q3, q2, margin))
                )
        else:
           # else z0 and z1 and z2 and z3, i.e this == v == (0, 0, 0, 0)
           return True

    def makeOrthogonalTo(this, v):
        """
        Returns the modification of this vector orthogonal to v, while keeping them in the same plane.
        """
        # say        v = [vx, vy, vz, vw]
        # and this = w = [wx, wy, wz, ww]
        # Now we change w into w' by a linear combination of v and w, so that w'
        # still lies in the plane spanned by v and w:
        # w' = p*v + q*w  with p,q are reals
        # i.e. w' = [p*vx + q*wx, p*vy + q*wy, p*vz + q*wz, p*vw + q*ww]
        #
        # Then w' and v are orthogonal if the dot product w'.v == 0
        # i.e.
        # vx(p*vx + q*wx) + vy(p*vy + q*wy) + vz(p*vz + q*wz) + vw(p*vw + q*ww)
        #                                                                 == 0
        # =>
        #
        # p(vx*vx + vy*vy + vw*vw + vz*vz) + q(vx*wx + vy*wy + vz*wz + vw*ww)
        #                                                                 == 0
        # =>
        #
        # p * (v.v) + q (v.w) == 0
        #
        # Now this holds if we choose
        #   p = - (v.w)
        #   q =   (v.v)
        p = - this * v  # dot product
        q = v * v       # dot product
        assert not this.isParallel(v, this.orthogonalMargin), 'null vector used or vectors are (too) parallel; this = ' + this.__repr__() + '; v = ' + v.__repr__()
        # TODO: is there a better way to set,...
        return vec(p * v + q * this)

    def cross(u, v, w):
        vw_xy = v.x * w.y - v.y * w.x
        vw_xz = v.x * w.z - v.z * w.x
        vw_xw = v.x * w.w - v.w * w.x
        vw_yz = v.y * w.z - v.z * w.y
        vw_yw = v.y * w.w - v.w * w.y
        vw_zw = v.z * w.w - v.w * w.z
        return vec(
            u.y * vw_zw  -  u.z * vw_yw  +  u.w * vw_yz,
            -u.x * vw_zw +  u.z * vw_xw  -  u.w * vw_xz,
            u.x * vw_yw  -  u.y * vw_xw  +  u.w * vw_xy,
            -u.x * vw_yz +  u.y * vw_xz  -  u.z * vw_xy
        )

    # The following function are needed to ensure the returned vector is of
    # Geom4d.vec and not cgtypes.vec4 (or cgkit_core.vec4)
    def __neg__(this, *args):
        return vec(cgtypes.vec4.__neg__(this, *args))

    def __add__(this, *args):
        return vec(cgtypes.vec4.__add__(this, *args))

    def __iadd__(this, *args):
        return vec(cgtypes.vec4.__iadd__(this, *args))

    def __sub__(this, *args):
        return vec(cgtypes.vec4.__sub__(this, *args))

    def __isub__(this, *args):
        return vec(cgtypes.vec4.__isub__(this, *args))

    # mul not needed, since the dot product returns a float

    def __imul__(this, *args):
        return vec(cgtypes.vec4.__imul__(this, *args))

    def __rmul__(this, *args):
        return vec(cgtypes.vec4.__rmul__(this, *args))

    def __div__(this, *args):
        return vec(cgtypes.vec4.__div__(this, *args))

    def __idiv__(this, *args):
        return vec(cgtypes.vec4.__idiv__(this, *args))

    def __mod__(this, *args):
        return vec(cgtypes.vec4.__mod__(this, *args))

    def __imod__(this, *args):
        return vec(cgtypes.vec4.__imod__(this, *args))

    def normalize(this, *args):
        return vec(cgtypes.vec4.normalize(this, *args))

    def normalise(this, *args):
        return vec(cgtypes.vec4.normalize(this, *args))

class Rotation:
    def __init__(this, v0, v1, alpha, beta = 0):
        """
        Define a rotation of alpha degrees in a plane set up by a span v0 and
        v1.
        
        v0 and v1 should not be parallel and should be of type Geom4D.vec
        The don't have to be orthogonal and do not have to be normalised.
        alpha: angle in radials for the rotation in the plane defined by v0 and
               v1. The rotational direction is ??
        beta: angle in radials for the rotation in the plane orthogonal to the
              plane spanned by v0 and v1.
        """
        this.setSpan(copy(v0), copy(v1))
        this.setAngle(alpha, beta)

    def setSpan(this, v0, v1):
        """Define the vectors that spans the plane
        """
        # check if v0 and v1 are parellel:
        # TODO
        #if v0
        # Make v0 and v1 orthogonal.
        this.v0 = v0
        this.v1 = v1
        this.e0 = v0.normalise()
        this.e1 = v1.makeOrthogonalTo(v0).normalise()
        this.MoUp2Date = False

    def setAngle(this, alpha, beta = 0):
        """
        Set the rotation angles. for the double (or Clifford) rotation.

        alpha: angle in radials for the rotation in the plane defined by v0 and
               v1. The rotational direction is ??
        beta: angle in radials for the rotation in the plane orthogonal to the
              plane spanned by v0 and v1.
        """
        this.alphaOrg = alpha
        this.alpha = alpha
        this.betaOrg = beta
        this.beta = beta
        this.MrUp2Date = False

    def getAngles(this):
        """
        Returns the tuple holding the current angles.
        """
        return (this.alphaOrg, this.betaOrg)

    def _setOrthoMatrix(this):
        """Get an orthogonal matrix that transfers the coordinate system to the
        new coordinate system induces by the span

        The matrix will map
          - [1, 0, 0, 0] on a normalised v0
          - [0, 1, 0, 0] on e1 where e1 is an orthogonal unit vector in the
                         plane spanned by v0 and v1
          - [0, 0, 1, 0] and [0, 0, 0, 1] on orthogonal unit vectors (i.e. they
                         are orthogonal to e0 and e1 and orthogonal between
                         themselves.
        """
        # Define 2 more orthogonal unit vectors e2 and e3
        # Define the matrix [e0 e1 e2 e3]
        # This matrix A will map
        # [1, 0, 0, 0] on e0 and
        # [0, 1, 0, 0] on e1 and
        # [0, 0, 1, 0] on e2 and
        # [0, 0, 0, 1] on e3.
        # 
        # Now what you want is a matrix A_inverse that maps e0 on the x-axis and
        # e1 on the y-axis. Then you want to rotate in the XOY plane and then
        # use A to rotate back again.
        #
        # Initialise v2 so that e0 . v2 = 0 then call v2.makeOrthogonalTo(e1) and
        # normalise.
        # if there is an i for which e0[i] == 0 initialising v2 is easy, just
        # define v2[i] = 1 and v2[j] = 0 for j != i
        # However v2 may not be parallel to e1.
        # If this is the case, then we can exchange the roll of e0 and e1:
        # E.G. e0 = [1/2, 1/2, 1/V2, 0] and e1 = [0, 0, 0, 1]
        # Then we would initialise v2 = [0, 0, 0, 1]
        # However v2 == e1 and it will be impossible to call
        # v2.makeOrthogonalTo(e1)
        # Instead set e0 = [0, 0, 0, 1] and e1 = [1/2, 1/2, 1/V2, 0]
        # And initialise v2 = [1, 0, 0, 0] and call v2.makeOrthogonalTo(e1)
        # If 4 all i e0[i] != 0,
        # then v2[i] = t . [1/e0[0], 1/e0[1], 1/e0[2], 1/e0[3]]
        # where t can be any permutation of [1, 1, -1, -1]
        # Choose that t for which v2 not parallel to e1
        #
        # There we go:
        zeroMargin = 1.0e-15
        def getZeroIndex(v, s = 0):
            """
            Get the index of the element that equals to 0 in vec v. If there
            none, -1 is returned.

            s: start with (incl) position s
            """
            zeroIndex = -1
            #print this.__class__, 'getZeroIndex', v, s
            for i in range(s, 4):
                if Geom3D.eq(v[i], 0, zeroMargin):
                    zeroIndex = i
                    break
            return zeroIndex
        def getUnitVector(i):
            """
            Returns a vector v of type vec for which v[i] = 1 and v[j] = 0 for j != i.
            """
            v = vec(0)
            v[i] = 1
            return v

        oopsMsg = "Ooops, this shouldn't happen!!"

        # status: a status dict that expresses the status after previous
        #         calls. The dict contains the fields:
        #         sz_e0: Search done for elements equal to 0 in e0 until (incl)
        #                the specified index. Initialise at -1.
        #         sz_e1: Search done for elements equal to 0 in e1 until (incl)
        #                the specified index. Initialise at -1.
        #         e0_z_e1: Expresses whether e0 and e1 were functionally
        #                  exchanged.
        #                  - Initialise at 0, which means they were not
        #                    exchanged.
        #                  - 1 means the were exchanged because e1 contains
        #                    one 1 and 3 0's (even though this might hold for e0
        #                    too)
        #                  - 2 means that they were exchanged because e1
        #                    contained a 0 and e0 didn't.
        #         sp: start looking in the permutation table at index.
        #             Initialise at 0.
        status = { 'sz_e0': -1, 'sz_e1': -1, 'e0_z_e1': 0, 'sp': 0 }

        # define e0 and e1 locally to be able to exchange their roll just for
        # calculating e2 and e3.
        e0, e1 = this.e0, this.e1

        # Now define e2,..
        zi    = getZeroIndex(e0)
        if zi > -1: # if e0 contains a 0 (zero)
            v2 = getUnitVector(zi)
            if v2.isParallel(e1, zeroMargin):
                # exchange e0 and e1 and repeat, since we know that e1 has 3 0's
                e0, e1 = e1, e0
                status['e0_z_e1'] = 1
                zi = getZeroIndex(e0)
                if zi > -1:
                    v2 = getUnitVector(zi)
                    if v2.isParallel(e1, zeroMargin):
                        # ok, e0 had 3 zeros as well,...
                        zi = getZeroIndex(e0, zi+1)
                        if zi > -1:
                            v2 = getUnitVector(zi)
                            assert not v2.isParallel(e1, zeroMargin), oopsMsg
                        else:
                            assert False, oopsMsg
                else:
                    assert False, oopsMsg
            status['sz_e0'] = zi
        else:
            status['sz_e0'] = 3
            zi = getZeroIndex(e1)
            if zi > -1:  # if e1 contains a 0 (zero)
                v2 = getUnitVector(zi)
                e0, e1 = e1, e
                status['e0_z_e1'] = 2
                assert not v2.isParallel(e1, zeroMargin), "Ooops, this shouldn't happen!!"
                status['sz_e1'] = zi
            else:
                vnIni = vec(1/e0[0], 1/e0[1], 1/e0[2], 1/e0[3])
                possiblePermuations = [
                    vec( vnIni[0],  vnIni[1], -vnIni[2], -vnIni[3]),
                    vec( vnIni[0], -vnIni[1],  vnIni[2], -vnIni[3]),
                    vec(-vnIni[0],  vnIni[1],  vnIni[2], -vnIni[3]),
                    vec( vnIni[0], -vnIni[1], -vnIni[2],  vnIni[3]), # this might be used later for e3
                    # I don't think these are necessary:
                    #vec(-vnIni[0],  vnIni[1], -vnIni[2],  vnIni[3]),
                    #vec(-vnIni[0], -vnIni[1],  vnIni[2],  vnIni[3])
                ]
                v2Found = False
                i = -1
                while not v2Found:
                    i += 1
                    assert i < len(possiblePermuations), "Oops, more permutations needed"
                    v2 = possiblePermuations[i]
                    v2Found = not v2.isParallel(e1, zeroMargin)
                status['sp'] = i + 1

        # Now the plane spanned by e1 and v2 is orthogonal to e0, as a
        # consequence the following operation will keep v2 orthogonal to e0:
        this.e2 = v2.makeOrthogonalTo(e1).normalise()

        # Use cross product for e3:
        v3 = this.e0.cross(this.e1, this.e2)
        # Normalisation should not be needed, but improves precision.
        #print this.__class__, '_setOrthoMatrix: v3', v3
        # TODO
        # Prehaps this should only steered by caller by setting hjigh precision.
        this.e3 = v3.normalise()
        #print 'e3', this.e3

#        # do something similar with e3:
#        # The code is partly copied and adjusted. No function is used to keep
#        # the code readable.
#        found = lambda v3, e1, e2: not (
#                v3.isParallel(e1, zeroMargin)
#                or
#                v3.isParallel(e2, zeroMargin)
#            )
#        v3Found = False
#        zi = status['sz_e0']
#        while not v3Found and zi < 3:
#            zi = getZeroIndex(e0, zi + 1)
#            if zi > -1: # if e0 contains a 0 (zero)
#                v3 = getUnitVector(zi)
#                v3Found = found(v3, e1, this.e2)
#                print 'v3Found:', v3Found, 'e2', this.e2 , 'v3', v3 
#            else:
#                zi = 3
#        if not v3Found:
#            # even if status['e0_z_e1'] == 1, it has no use to search for more
#            # 0's in e1 (old e0), since e0 (old e1) already contained 3 which
#            # are investigated in the loop above.
#            if status['e0_z_e1'] == 0:
#                # switch and investigate
#                e0, e1 = e1, e0
#                zi = status['sz_e1']
#                # TODO: reuse, since the above loop is copied here.
#                while not v3Found and zi < 3:
#                    zi = getZeroIndex(e0, zi + 1)
#                    if zi > -1: # if e0 contains a 0 (zero)
#                        v3 = getUnitVector(zi)
#                        v3Found = found(v3, e1, this.e2)
#                    else:
#                        zi = 3
#        if not v3Found:
#            i = status['sp']
#            while not v3Found:
#                i += 1
#                assert i < len(possiblePermuations), "Oops, more permutations needed"
#                v3 = vnIni * possiblePermuations[i]
#                v3Found = found(v3, e1, this.e2)

        # Now the plane spanned by e1 and v3 is orthogonal to e0, as a
        # consequence the following operation will keep v3 orthogonal to e0:
        v3 = v3.makeOrthogonalTo(e1)
        # Similarly
        # Now the plane spanned by e2 and v3 is orthogonal to e0 and e1, as a
        # consequence the following operation will keep v3 orthogonal to e0 and
        # e1:
        this.e3 = v3.makeOrthogonalTo(this.e2).normalise()
        this._Mo  = cgtypes.mat4(this.e0, this.e1, this.e2, this.e3)
        if this._Mo.determinant() < 0:
            # Oops we created a reflection by switching axes, the handedness is
            # not preserved. Switch the two axes e0 and e1 and rotate in the
            # opposite direction.
            #print "fixing handedness"
            this._Mo  = cgtypes.mat4(this.e1, this.e0, this.e2, this.e3)
            this.alpha = -this.alphaOrg
        #print '---vvv---orthoMatrix---vvv---'
        #print this._Mo, 'with determinant:', this._Mo.determinant()
        #print '---^^^---orthoMatrix---^^^---'
        this._MoT = this._Mo.transpose()
        this.MoUp2Date = True

    def exchangePlanes(this):
        if not this.MoUp2Date:
            this._setOrthoMatrix()
        # exchange planes (e0, e1) and (e2, e3) with keeping the determinant
        this.e0, this.e1, this.e2, this.e3 = this.e3, this.e2, this.e0, this.e1
        this._Mo  = cgtypes.mat4(this.e0, this.e1, this.e2, this.e3)
        this._MoT = this._Mo.transpose()

    def setMatrix(this):
        """
        Calculates and sets the rotation matrix for the current settings.
        """
        if not this.MoUp2Date:
            this._setOrthoMatrix()
        if not this.MrUp2Date:
            this._Mr = cgtypes.mat4(1.0)
            cos = math.cos(this.alpha)
            sin = math.sin(this.alpha)
            this._Mr[0, 0] = cos
            this._Mr[0, 1] = -sin
            this._Mr[1, 0] = sin
            this._Mr[1, 1] = cos
            if this.beta != 0:
                cos = math.cos(this.beta)
                sin = math.sin(this.beta)
                this._Mr[2, 2] = cos
                this._Mr[2, 3] = -sin
                this._Mr[3, 2] = sin
                this._Mr[3, 3] = cos
            this.MrUp2Date = True
        this.M = this._Mo * this._Mr * this._MoT

    def getMatrix(this):
        if not this.MrUp2Date or not this.MoUp2Date:
            this.setMatrix()
        return this.M

# TODO continue with: make a nice 4D rotation interface and add this to std view
# settings. Then convert all older 4D scenes and remove old stuff from Geom3D.
class SimpleShape:
    dbgPrn = False
    dbgTrace = False
    className = "Geom4D.SimpleShape"
    def __init__(this, Vs, Cs, Es = [], Ns = [], colors = ([], []), name = "4DSimpleShape"):
        """
        Cs: and array of cells, consisting of an array of Fs.
        """
        if this.dbgTrace:
            print '%s.SimpleShape.__init__(%s,..):' % (this.__class__name)
        this.dimension = 4
        this.v = Geom3D.Fields()
        this.e = Geom3D.Fields()
        this.f = Geom3D.Fields()
        this.c = Geom3D.Fields()
        # SETTINGS similar to Geom3D.SimpleShape:
        #print 'SimpleShape.Fs', Fs
        this.name = name
        if colors[0] == []:
            colors = ([rgb.red[:]], [])
        # if this.mapToSingeShape = False each cell is mapped to one 3D shape
        # and the edges are mapped to one shape as well. The disadvantage is
        # that for each shape glVertexPointer is set, while if
        # this.mapToSingeShape = True is set to True one vertex array is used.
        this.mapToSingeShape = True
        # if useTransparency = False opaque colours are used, even if they
        # specifically set to transparent colours.
        this.useTransparency(True)
        this.setVertexProperties(Vs = Vs, Ns = Ns, radius = -1., color = [1. , 1. , .8 ])
        this.setFaceProperties(
            colors = colors, drawFaces = True
        )
        this.glInitialised = False
        # SETTINGS 4D specific:
        this.setCellProperties(
            Cs = Cs, colors = colors, drawCells = False, scale = 1.0
        )
        # For initialisation setCellProperties needs to be called before
        # setEdgeProperties, since the latter will check the scale value
        this.setEdgeProperties(
            Es = Es, radius = -1., color = [0.1, 0.1, 0.1],
            drawEdges = True, showUnscaled = True
        )
        this.setProjectionProperties(11.0, 10.0)
        this.M4 = None # expresses whether the 4D coordinates need to be updated
        this.projectedTo3D = False
        if this.dbgPrn:
            print '%s.__init__(%s,..)' % (this.__class__, this.name)
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
                this.Vs  = [ cgtypes.vec4(v) for v in dict['Vs'] ]
            if 'Ns' in dict and dict['Ns'] != None:
                this.Ns  = [ cgtypes.vec4(n) for n in dict['Ns'] ]
                #assert len(this.Ns) == len(this.Vs)
            if 'radius' in dict and dict['radius'] != None:
                this.v.radius = dict['radius']
            if 'color' in dict and dict['color'] != None:
                this.v.col = dict['color']
            this.projectedTo3D = False

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
            'radius': this.v.radius,
            'color': this.v.col,
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
                this.projectedTo3D = False
            if 'radius' in dict and dict['radius'] != None:
                this.e.radius = dict['radius']
                this.projectedTo3D = False
            if 'color' in dict and dict['color'] != None:
                this.e.col = dict['color']
                this.projectedTo3D = False
            if 'drawEdges' in dict and dict['drawEdges'] != None:
                try:
                    currentSetting = this.e.draw
                except AttributeError:
                    currentSetting = None
                if currentSetting != dict['drawEdges']:
                    this.projectedTo3D = this.projectedTo3D and not (
                            # if all the below are true, then the edges need
                            # extra Vs, which means we need to reproject.
                            this.c.scale < 1.0
                            and 
                            # .. and if the CURRENT settings is show unscaled
                            # (Though changes in this setting might mean that
                            # new projection was not needed)
                            this.e.showUnscaled
                        )
                    if this.projectedTo3D:
                        # Try is needed,
                        # not for the first time, since then this.projectedTo3D
                        # will be False
                        # but because of the this.mapToSingeShape setting.
                        try:
                            this.cell.setEdgeProperties(drawEdges = dict['drawEdges'])
                        except AttributeError:
                            pass
                this.e.draw = dict['drawEdges']
            if 'showUnscaled' in dict and dict['showUnscaled'] != None:
                this.projectedTo3D = this.projectedTo3D and not (
                        # if all the below are true, then a change in unscaled
                        # edges means a changes in Vs, since the extra edges
                        # have different Vs. This means we need to reproject.
                        this.e.draw
                        and
                        this.c.scale < 1.0
                        and 
                        this.e.showUnscaled != dict['showUnscaled']
                    )
                this.e.showUnscaled = dict['showUnscaled']

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
                'radius': this.e.radius,
                'color': this.e.col,
                'drawEdges': this.e.draw
            }

    def recreateEdges(this):
        """
        Recreates the edges in the 3D object by using an adges for every side of
        a face, i.e. all faces will be surrounded by edges.

        Edges will be filtered so that shared edges between faces,
        i.e. edges that have the same vertex index, only appear once.
        The creation of edges is not optimised and can take a long time.
        """
        assert False, "Geom4D.SimpleShape.recreateEdges: TODO IMPLEMENT"

    def setFaceProperties(this, dictPar = None, **kwargs):
        """
        Define the properties of the faces.

        Accepted are the optional (keyword) parameters:
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
        loc = '%s.setFaceProperties(%s,..): warning' % (this.__class__, this.name)
        if this.dbgTrace:
            print loc
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Fs' in dict and dict['Fs'] != None:
                print '%s: FS not supported, use Cs instead' % (loc)
            if 'colors' in dict and dict['colors'] != None:
                this.f.col = (dict['colors'])
            if 'drawFaces' in dict and dict['drawFaces'] != None:
                this.f.draw = dict['drawFaces']
            this.projectedTo3D = False

    def getFaceProperties(this):
        """
        Return the current face properties as can be set by setFaceProperties.

        Returned is a dictionary with the keywords colors, and drawFaces.
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
        NOTE: these settings can be overwritten by setCellProperties, see
        setCellProperties (or getCellProperties).
        """
        if this.dbgTrace:
            print '%s.getFaceColors(%s,..):' % (this.__class__, this.name)
        return {
                'colors': this.f.col,
                'drawFaces': this.f.draw
            }

    def setCellProperties(this, dictPar = None, **kwargs):
        """
        Define the properties of the cells.

        Accepted are the optional (keyword) parameters:
          - Cs
          - colors,
          - drawCells
          - scale: scale is the new scaling factor (i.e. it will not be
            multiplied by the current scaling factor)
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equal to None) they are not changed.
        See getCellProperties for the explanation of the keywords.
        The output of getCellProperties can be used as the dictPar parameter.
        This can be used to copy settings from one shape to another.
        If dictPar is used and kwargs, then onl    dbgPrn = False
    dbgTrace = False
    className = "SimpleShape"y the dictPar will be used.
        """
        if this.dbgTrace:
            print '%s.setCellProperties(%s,..):' % (this.__class__, this.name)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else: 
                dict = kwargs
            if 'Cs' in dict and dict['Cs'] != None:
                this.Cs = dict['Cs']
            if 'colors' in dict and dict['colors'] != None:
                this.c.col = dict['colors']
            if 'drawCells' in dict and dict['drawCells'] != None:
                this.c.draw = dict['drawCells']
            if 'scale' in dict and dict['scale'] != None:
                this.c.scale = dict['scale']
            #print 'Cs:', this.Cs
            #print 'this.c.col[1]:', this.c.col[1]
            # TODO Is an assert valid here:
            #assert len(this.Cs) == len(this.c.col[1]), 'len(Cs) = %d != %d = (c.col[1])' % (len(this.Cs), len(this.c.col[1]))
            this.projectedTo3D = False

    def getCellProperties(this, Cs = None, colors = None):
        """
        Return the current face properties as can be set by setCellProperties.

        Cs: optional array of cells. Each cell consists of an array of faces,
            that do not need to be triangular. It is a hierarchical array, ie it
            consists of sub-array, where each sub-array describes one face. Each
            n-sided face is desribed by n indices. Empty on default. Using
            triangular faces only gives a better performance.
            If Cs == None, then the previous specified value will be used.
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each cell with
                   index 'i' in Cs which colour index from the parameter color
                   is used for this face. If empty then colors[0][0] shall be
                   used for each face.
                   It should have the same length as Cs (or the current cells if
                   Cs not specified) otherwise the parameter is ignored and the
                   cell colors are set by some default algorithm.
        drawCells: settings that expresses whether the cells should be drawn. If
                   cells are drawn, then the individual faces of the cell will
                   not be drawn. I.e. it overwrites the color settings in
                   setFaceProperties
        scale: scale the cell with the specified scaling factor around its
               gravitational centre. This factor is typically <= 1.
        """
        if this.dbgTrace:
            print '%s.getCellProperties(%s,..):' % (this.__class__, this.name)
        return {
                'Cs': this.Cs,
                'colors': this.c.col,
                'drawCells': this.c.draw,
                'scale': this.c.scale
            }

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
        this.projectedTo3D   = False

    def rotate(this, rotation, successive = False):
        """
        Rotate the polychoron by the specified rotation.

        rotation: a rotation of type Geom4D.Rotation.
        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        M = rotation.getMatrix()
        if not successive or this.M4 == None: this.M4 = M
        else: this.M4 = M * this.M4
        this.projectedTo3D = False

    def rotateInStdPlane(this, plane, angle, successive = False):
        """
        Rotate in a plane defined by 2 coordinate axes.

        plane: one of Plane.XY, Plane.XZ, Plane.XW, Plane.YZ,
               Plane.YW, Plane.ZW
        angle: the angle in radials in counter-clockwise direction, while the
               Plane.PQ has a horizontal axis P pointing to the right and a
               vertical axis Q pointing up.
        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        c =  math.cos(angle)
        s = -math.sin(angle)
        M = cgtypes.mat4(1.0)
        if   Axis.X & plane:
            i = 0
            if   Axis.Y & plane: j = 1
            elif Axis.Z & plane: j = 2
            else                    : j = 3
        elif Axis.Y & plane:
            i = 1
            if   Axis.Z & plane: j = 2
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
        this.projectedTo3D = False

    def projectVsTo3D(this, Vs4D):
        """
        returns an array of 3D vertices.
        """
        #print "projectTo3D_getVs"
        Vs3D = []
        for v in Vs4D:
            wV = v[3]
            #print "mapping v:", v
            if not Geom3D.eq(this.wCamera, wV):
                scale = this.wCameraDistance / (this.wCamera - wV)
                Vs3D.append([scale * v[0], scale * v[1], scale * v[2]])
            else:
                Vs3D.append([1e256, 1e256, 1e256])
        return Vs3D

    def applyTransform(this):
        """
        Apply current transformation to the current vertices and returns the
        result.

        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """

    def useTransparency(this, use):
        this.removeTransparency = not use
        this.updateTransparency = True

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
        if not this.glInitialised:
            this.glInit()
        if this.mapToSingeShape:
            this.glDrawSingleRemoveUnscaledEdges()
            this.cell.glDraw()
        else:
            this.glDrawSplit()
            for cell in this.cells:
                cell.glDraw()

    def glDrawSingleRemoveUnscaledEdges(this):
        isScaledDown = not Geom3D.eq(this.c.scale, 1.0, margin = 0.001)
        if not this.projectedTo3D:
            # print 'reprojecting...'
            try:
                del this.cell
            except AttributeError:
                pass
            Ns3D = []
            if this.M4 != None:
                Vs4D = [this.M4*v for v in this.Vs]
            # TODO fix Ns.. if needed..
            #    if this.Ns != []:cleanUp
            #        Ns4D = [this.M4*n for n in this.Ns]
            else:
                Vs4D = [v for v in this.Vs]
            Vs3D = this.projectVsTo3D(Vs4D)
            #for i in range(0, len(this.Es), 2):
            #    v0 = Vs4D[this.Es[i]]
            #    v1 = Vs4D[this.Es[i+1]]
            #    print 'delta v:', v0 - v1
            #    print 'Edge [%d, %d]; len:' % (this.Es[i], this.Es[i+1]), (v1-v0).length()
            #if this.Ns != []:
            #    Ns3D = this.projectVsTo3D(Ns4D)
            # Now project all to one 3D shape. 1 3D shape is chosen, instean of
            # projecting each cell to one shape because of different reasons:
            #  - when drawing transparent faces all the opaqe fae should be
            #    drawn first.
            #  - if drawing the cells per shape, the glVertexPointer should be
            #    called for each cell. (Currently SimpleShape will not call this
            #    function unless the vertices have been changed...
            shapeVs = []
            shapeEs = []
            shapeFs = []
            shapeColIndices = []
            if this.c.draw:
                shapeCols = this.c.col[0]
            else:
                shapeCols = this.f.col[0]
            if this.removeTransparency:
                shapeCols = [ c[0:3] for c in shapeCols ]
            if this.e.draw and (not isScaledDown or this.e.showUnscaled):
                shapeVs = Vs3D
                shapeEs = this.Es
            # Add a shape with faces for each cell
            for i in xrange(len(this.Cs)):
                # use a copy, since we will filter (v indices will change):
                cellFs = [ f[:] for f in this.Cs[i]]
                if this.c.draw:
                    shapeColIndices.extend([this.c.col[1][i] for f in cellFs])
                else:
                    shapeColIndices.extend(this.f.col[1][i])
                # Now cleanup Vs3D
                # TODO
                # if this.e.draw and (not isScaledDown or this.e.showUnscaled):
                # Then shapeVs = Vs3D already, and the code below is all
                # unecessary.
                cellVs = Vs3D[:]
                nrUsed = glue.cleanUpVsFs(cellVs, cellFs)
                # Now attaching to current Vs, will change index:
                offset = len(shapeVs)
                cellFs = [[vIndex + offset for vIndex in f] for f in cellFs]
                # Now scale from gravitation centre:
                if isScaledDown:
                    g = cgtypes.vec3(0, 0, 0)
                    sum = 0
                    for vIndex in range(len(cellVs)):
                        g = g + nrUsed[vIndex] * cgtypes.vec3(cellVs[vIndex])
                        sum = sum + nrUsed[vIndex]
                    if sum != 0:
                        g = g / sum
                    #print this.name, 'g:', g
                    cellVs = [this.c.scale * (cgtypes.vec3(v) - g) + g for v in cellVs]


                shapeVs.extend(cellVs)
                shapeFs.extend(cellFs)
                # for shapeColIndices.extend() see above
            this.cell = Geom3D.SimpleShape(
                    shapeVs, shapeFs, shapeEs, [], # Vs , Fs, Es, Ns
                    (shapeCols, shapeColIndices),
                    name = '%s_projection' % (this.name)
                )
            this.cell.setVertexProperties(radius = this.v.radius, color = this.v.col)
            this.cell.setEdgeProperties(radius = this.e.radius, color = this.e.col, drawEdges = this.e.draw)
            this.cell.setFaceProperties(drawFace = this.f.draw)
            this.cell.glInitialised = True # done as first step in this func
            this.projectedTo3D = True
            this.updateTransparency = False
            if this.e.draw and isScaledDown:
                this.cell.recreateEdges()
                # Don't use, out of performance issues:
                # cellEs = this.cell.getEdgeProperties()['Es']
                # --------------------------
                # Bad performance during scaling:
                # cellEs = this.cell.getEdgeProperties()['Es']
                # this.cell.recreateEdges()
                # cellEs.extend(this.cell.getEdgeProperties()['Es'])
                # -------end bad perf---------
                cellEs = this.cell.Es
                if this.e.showUnscaled:
                    cellEs.extend(this.Es)
                this.cell.setEdgeProperties(Es = cellEs)
        if this.updateTransparency:
            cellCols = this.cell.getFaceProperties()['colors']
            if this.removeTransparency:
                shapeCols = [ c[0:3] for c in cellCols[0] ]
            else:
                if this.c.draw:
                    shapeCols = this.c.col[0]
                else:
                    shapeCols = this.f.col[0]
            cellCols = (shapeCols, cellCols[1])
            this.cell.setFaceProperties(colors = cellCols)
            this.updateTransparency = False

    def glDrawSplit(this):
        if not this.projectedTo3D:
            try:
                del this.cells
            except AttributeError:
                pass
            Ns3D = []
            if this.M4 != None:
                Vs4D = [this.M4*v for v in this.Vs]
            # TODO fix Ns.. if needed..
            #    if this.Ns != []:
            #        Ns4D = [this.M4*n for n in this.Ns]
            else:
                Vs4D = [v for v in this.Vs]
            Vs3D = this.projectVsTo3D(Vs4D)
            #if this.Ns != []:
            #    Ns3D = this.projectVsTo3D(Ns4D)
            this.cells = []
            # Add a cell for just the edges:
            if this.e.draw:
                cell = Geom3D.SimpleShape(
                        Vs3D, [], this.Es, [], # Vs , Fs, Es, Ns
                        name = '%s_Es' % (this.name)
                    )
                cell.setVertexProperties(radius = this.v.radius, color = this.v.col)
                cell.setEdgeProperties(radius = this.e.radius, color = this.e.col, drawEdges = this.e.draw)
                cell.setFaceProperties(drawFaces = False)
                cell.glInitialised = True
                this.cells.append(cell)
            # Add a shape with faces for each cell
            for i in xrange(len(this.Cs)):
                if this.c.draw:
                    colors = (this.c.col[0][this.c.col[1][i]], [])
                else:
                    colors = (this.f.col[0], this.f.col[1][i])
                #print colors
                cell = Geom3D.SimpleShape(
                        Vs3D, this.Cs[i], [], [], # Vs , Fs, Es, Ns
                        colors,
                        name = '%s_%d' % (this.name, i)
                    )
                # The edges and vertices are drawn through a separate shape below.
                cell.setVertexProperties(radius = -1)
                cell.setEdgeProperties(drawEdges = False)
                cell.setFaceProperties(drawFace = this.f.draw)
                cell.scale(this.c.scale)
                cell.glInitialised = True
                this.cells.append(cell)
            this.projectedTo3D = True

    def toPsPiecesStr(this,
            faceIndices = [],
            scaling = 1,
            precision = 7,
            margin = 1.0e5*Geom3D.defaultFloatMargin,
            pageSize = PS.PageSizeA4
        ):
        if this.mapToSingeShape:
            return this.cell.toPsPiecesStr(faceIndices, scaling, precision, margin, pageSize)
        else:
            assert False, 'toPsPiecesStr not supported for mapping to split draw'

# Tests:
if __name__ == '__main__':
    import os

    wDir = 'tstThis'
    cwd = os.getcwd()

    if not os.path.isdir(wDir):
        os.mkdir(wDir, 0775)
    os.chdir(wDir)

    NrOfErrorsOcurred = 0
    def printError(str):
        global NrOfErrorsOcurred
        print '***** ERROR while testing *****'
        print ' ', str
        NrOfErrorsOcurred += 1

    v = vec(1, 1, 0, 0)
    w = vec(0, 3, 4, 0)
    z = 0.1 * w
    p = z.isParallel(w)
    if not p:
        printError('in function isParallel')
    t = w.makeOrthogonalTo(v)
    #print 'check if [-3, 3, 8, 0] ==', w
    if not (
        Geom3D.eq(t.x, -3) and
        Geom3D.eq(t.y, 3) and
        Geom3D.eq(t.z, 8) and
        Geom3D.eq(t.w, 0)
    ):
        printError('in function makeOrthogonalTo')
        print '  Expected (-3, 3, 8, 0), got', t

    n = w.normalise()
    
    # check if n is still of type vec and not cgtypes.vec4 (which doesn't have
    # a isParallel)
    if not n.isParallel(w):
        printError('in function isParallel after norm')

    def testOrthogonalVectors (R, margin = Geom3D.defaultFloatMargin):
        if not Geom3D.eq(R.e0 * R.e1, 0.0, margin):
            printError('in function _setOrthoMatrix: e0.e1 = ', R.e0*R.e1, '!= 0')
        if not Geom3D.eq(R.e0 * R.e2, 0.0, margin):
            printError('in function _setOrthoMatrix: e0.e2 = ', R.e0*R.e2, '!= 0')
        if not Geom3D.eq(R.e0 * R.e3, 0.0, margin):
            printError('in function _setOrthoMatrix: e0.e3 = ', R.e0*R.e3, '!= 0')
        if not Geom3D.eq(R.e1 * R.e2, 0.0, margin):
            printError('in function _setOrthoMatrix: e1.e2 = ', R.e1*R.e2, '!= 0')
        if not Geom3D.eq(R.e1 * R.e3, 0.0, margin):
            printError('in function _setOrthoMatrix: e1.e3 = ', R.e1*R.e3, '!= 0')
        if not Geom3D.eq(R.e2 * R.e3, 0.0, margin):
            printError('in function _setOrthoMatrix: e2.e3 = ', R.e2*R.e3, '!= 0')
        print '-----resulting matrix-----'
        print R.getMatrix()
        print '--------------------------'

    r = Rotation(v, w, math.pi/4)
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    r = Rotation(vec(0, 0, 1, 0), vec(0, 1, 0, 0), math.pi/4)
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    # error in this one:
    #r = Rotation(vec(0, 1, 0, 0), vec(0, 0, 1, 0), math.pi/4)
    # ok:
    #r = Rotation(vec(1, 0, 0, 0), vec(0, 0, 1, 0), math.pi/4)
    # not ok:
    r = Rotation(vec(0, 0, 1, 0), vec(1, 0, 0, 0), math.pi/4)
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    r = Rotation(vec(0, 0, 0, 1), vec(1, 0, 0, 0), math.pi/4)
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    r = Rotation(vec(0, 0, 0, 1), vec(1, 0, 0, 0), math.pi/4, math.atan(0.75))
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    # EOT
    if NrOfErrorsOcurred == 0:
        print 'test OK'
    else:
        print 'test failed with %d error(s)' % NrOfErrorsOcurred

# >>> from cgkit.cgtypes import vec4
# >>> print vec4.__dict__
# {'__module__': 'cgkit.cgtypes', '__doc__': "A 4-dimensional vector of floats.\n\n    This class is derived from the vec4 class in the _core module and\n    adds some missing stuff that's better done in Python.\n    ", '__init__': <function __init__ at 0xb7cd9ca4>}
# >>> print vec4.__bases__
# (<class 'cgkit._core.vec4'>,)
# 
# >>> from cgkit._core import vec4
# >>> print vec4.__dict__
# {'__module__': 'cgkit._core', '__repr__': <Boost.Python.function object at 0x81e4348>, '__ne__': <Boost.Python.function object at 0x81e41f8>, '__str__': <Boost.Python.function object at 0x81e4310>, '__gt__': <Boost.Python.function object at 0x81e42a0>, '__reduce__': <Boost.Python.function object at 0x81e3560>, 'maxAbsIndex': <Boost.Python.function object at 0x81e5000>, 'maxIndex': <Boost.Python.function object at 0x81e4f20>, '__rmul__': <Boost.Python.function object at 0x81e4578>, '__lt__': <Boost.Python.function object at 0x81e4230>, '__imod__': <Boost.Python.function object at 0x81e4498>, '__init__': <Boost.Python.function object at 0x81e3d80>, 'normalize': <Boost.Python.function object at 0x81e4e40>, 'min': <Boost.Python.function object at 0x81e4e78>, 'minAbsIndex': <Boost.Python.function object at 0x81e4fc8>, 'length': <Boost.Python.function object at 0x81e4e08>, '__abs__': <Boost.Python.function object at 0x81e4dd0>, '__pos__': <Boost.Python.function object at 0x81e4d20>, '__safe_for_unpickling__': True, '__getinitargs__': <Boost.Python.function object at 0x81e5038>, '__doc__': None, '__len__': <Boost.Python.function object at 0x81e4d48>, 't': <property object at 0xb7d7066c>, 'minIndex': <Boost.Python.function object at 0x81e4ee8>, '__isub__': <Boost.Python.function object at 0x81e43b8>, '__getitem__': <Boost.Python.function object at 0x81e4d70>, 'maxAbs': <Boost.Python.function object at 0x81e4f90>, 'max': <Boost.Python.function object at 0x81e4eb0>, '__idiv__': <Boost.Python.function object at 0x81e4428>, '__setitem__': <Boost.Python.function object at 0x81e4d98>, '__add__': <Boost.Python.function object at 0x81e44d0>, 'x': <property object at 0xb7d705cc>, 'minAbs': <Boost.Python.function object at 0x81e4f58>, '__eq__': <Boost.Python.function object at 0x81e46c8>, '__imul__': <Boost.Python.function object at 0x81e43f0>, '__mod__': <Boost.Python.function object at 0x81e4690>, '__instance_size__': 40, '__neg__': <Boost.Python.function object at 0x81e4540>, '__iadd__': <Boost.Python.function object at 0x81e4380>, '__div__': <Boost.Python.function object at 0x81e4620>, '__le__': <Boost.Python.function object at 0x81e4268>, '__mul__': <Boost.Python.function object at 0x81e45e8>, 'w': <property object at 0xb7d70644>, 'y': <property object at 0xb7d705f4>, '__sub__': <Boost.Python.function object at 0x81e4508>, 'z': <property object at 0xb7d7061c>, '__ge__': <Boost.Python.function object at 0x81e42d8>}
