#! /usr/bin/python
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
import indent

turn = lambda r: r * 2 * math.pi
radials = lambda r: math.pi * r / 180
degrees = lambda r: 180.0 * r   / math.pi

fullTurn = turn(1)
hTurn = turn(0.5)
qTurn = turn(0.25)
tTurn = turn(1.0/3)

eqFloatMargin = 1.0e-10
roundFloatMargin = 10

def eq(a, b):
    """
    Check if 2 floats 'a' and 'b' are close enough to be called equal.

    a: a floating point number.
    b: a floating point number.
    margin: if |a - b| < margin then the floats will be considered equal and
            True is returned.
    """
    return abs(a - b) < eqFloatMargin

def float2str(f, prec):
    """Convert float to string only using prec decimals

    Doesn't use unnecessary 0s

    prec: the amount of digits to use
    """
    fmt = '{{:.{}g}}'.format(prec)
    s = fmt.format(round(f, prec))
    # FIXME: there must be a better way of doing this:
    if s == "-0":
        s = "0"
    return s

# Use tuples instead of lists to enable building sets used for isometries

class Vec(tuple):
    def __new__(cls, v):
        return tuple.__new__(cls, [float(a) for a in v])

    def __repr__(self):
        s = indent.Str('%s(%s)' % (self.__class__.__name__, str(self)))
        if __name__ != '__main__':
            s = s.insert('%s.' % __name__)
        return s

    def __str__(self):
        try:
            s = '[%s' % self[0]
            for i in range(1, len(self)): s = '%s, %s' % (s, self[i])
            return '%s]' % s
        except IndexError:
            return '[]'

    def __add__(self, w):
        return self.__class__([a+b for a, b in zip(self, w)])

    def __radd__(self, w):
        # provide __radd__ for [..] + Vec([..])
        # print 'v', self, 'w', w
        return self.__class__([a+b for a, b in zip(self, w)])

    def __sub__(self, w):
        return self.__class__([a-b for a, b in zip(self, w)])

    def __rsub__(self, w):
        # provide __rsub__ for [..] + Vec([..])
        return self.__class__([b-a for a, b in zip(self, w)])

    def __eq__(self, w):
        #print '%s ?= %s' % (self, w)
        try:
            r = len(self) == len(w)
        except TypeError:
            #print 'info: comparing different types in Vec (%s and %s)' % (
            #        self.__class__.__name__, w.__class__.__name__
            #    )
            return False
        for a, b in zip(self, w):
            if not r: break
            r = r and eq(a, b)
            #print '%s ?= %s : %s (d = %s)' % (a, b, eq(a, b), a-b)
        return r

    def __ne__(self, w):
        return not self == w

    def __neg__(self):
        return self.__class__([-a for a in self])

    def __mul__(self, w):
        if isinstance(w, tuple):
            # dot product
            r = 0
            for a, b in zip(self, w): r += a*b
            return r
        elif isinstance(w, int) or isinstance(w, float):
            return self.__class__([w*a for a in self])

    def __rmul__(self, w):
        if isinstance(w, tuple):
            # provide __rmul__ for [..] + Vec([..])
            # dot product
            r = 0
            for a, b in zip(self, w): r += a*b
            return r
        if isinstance(w, int) or isinstance(w, float):
            return self.__class__([w*a for a in self])

    def __div__(self, w):
        if isinstance(w, int) or isinstance(w, float):
            return self.__class__([a/w for a in self])

    def squareNorm(self):
        r = 0
        for a in self: r += a*a
        return r

    def norm(self):
        return math.sqrt(self.squareNorm())

    def normalise(self):
        return self/self.norm()

    normalize = normalise

    def angle(self, w):
        return math.acos(self.normalise()*w.normalise())

    # TODO cross product from GA?

class Vec3(Vec):
    def __new__(cls, v):
        return Vec.__new__(cls, [float(v[i]) for i in range(3)])

    def cross(self, w):
        return self.__class__([
            self[1] * w[2] - self[2] * w[1],
            self[2] * w[0] - self[0] * w[2],
            self[0] * w[1] - self[1] * w[0]])

    # TODO implement Scenes3D.getAxis2AxisRotation here

ux = Vec3([1, 0, 0])
uy = Vec3([0, 1, 0])
uz = Vec3([0, 0, 1])

class Vec4(Vec):
    def __new__(cls, v):
        return Vec.__new__(cls, [float(v[i]) for i in range(4)])

    def isParallel(self, v):
        z0 = z1 = z2 = z3 = False # expresses whether self[i] == v[i] == 0
        q0, q1, q2, q3 = 1, 2, 3, 4 # initialise all differently
        try:
            q0 = self[0]/v[0]
        except ZeroDivisionError:
            z0 = eq(self[0], 0.0)
        try:
            q1 = self[1]/v[1]
        except ZeroDivisionError:
            z1 = eq(self[1], 0.0)
        try:
            q2 = self[2]/v[2]
        except ZeroDivisionError:
            z2 = eq(self[2], 0.0)
        try:
            q3 = self[3]/v[3]
        except ZeroDivisionError:
            z3 = eq(self[3], 0.0)
        if not z0:
            return (z1 or eq(q0, q1)) and \
                    (z2 or eq(q0, q2)) and \
                    (z3 or eq(q0, q3))
        elif not z1:
            return (z0 or eq(q1, q0)) and \
                (z2 or eq(q1, q2)) and \
                (z3 or eq(q1, q3))
        elif not z2:
            return (z0 or eq(q2, q0)) and \
                (z1 or eq(q2, q1)) and \
                (z3 or eq(q2, q3))
        elif not z3:
            return (z0 or eq(q3, q0)) and \
                (z1 or eq(q3, q1)) and \
                (z2 or eq(q3, q2))
        else:
            # else z0 and z1 and z2 and z3, i.e self == v == (0, 0, 0, 0)
            return True

    def makeOrthogonalTo(w, v):
        """
        Returns the modification of this vector orthogonal to v.

        While keeping them in the same plane.
        """
        # say v = [vx, vy, vz, vw]
        # and w = [wx, wy, wz, ww]
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
        p = - w * v  # dot product
        q = v * v       # dot product
        assert not w.isParallel(v), \
            'null vector used or vectors are (too) parallel; self = ' + \
            w.__repr__() + '; v = ' + v.__repr__()
        # TODO: is there a better way to set,...
        return Vec4(p * v + q * w)

    def cross(self, v, w):
        vw_xy = v[0] * w[1] - v[1] * w[0]
        vw_xz = v[0] * w[2] - v[2] * w[0]
        vw_xw = v[0] * w[3] - v[3] * w[0]
        vw_yz = v[1] * w[2] - v[2] * w[1]
        vw_yw = v[1] * w[3] - v[3] * w[1]
        vw_zw = v[2] * w[3] - v[3] * w[2]
        return Vec4([
            self[1]  * vw_zw -  self[2] * vw_yw  +  self[3] * vw_yz,
            -self[0] * vw_zw +  self[2] * vw_xw  -  self[3] * vw_xz,
            self[0]  * vw_yw -  self[1] * vw_xw  +  self[3] * vw_xy,
            -self[0] * vw_yz +  self[1] * vw_xz  -  self[2] * vw_xy
        ])

def unitVec4(i):
    v = [0, 0, 0, 0]
    v[i] = 1
    return Vec4(v)

class Quat(Vec):
    def __new__(cls, v=None):
        # if 3D vector, use it to set vector part only and use 0 for scalar part
        if len(v) == 3: v = [0, v[0], v[1], v[2]]
        return Vec.__new__(cls, [float(v[i]) for i in range(4)])

    def conjugate(v):
        return v.__class__([v[0], -v[1], -v[2], -v[3]])

    def __mul__(v, w):
        if isinstance(w, Quat):
            # Quaternion product
            return v.__class__([
                v[0]*w[0] - v[1]*w[1] - v[2] * w[2] - v[3] * w[3],
                v[0]*w[1] + v[1]*w[0] + v[2] * w[3] - v[3] * w[2],
                v[0]*w[2] - v[1]*w[3] + v[2] * w[0] + v[3] * w[1],
                v[0]*w[3] + v[1]*w[2] - v[2] * w[1] + v[3] * w[0]])
        elif isinstance(w, int) or isinstance(w, float):
            return Vec.__mul__(v, w)

    def dot(v, w):
        return Vec.__mul__(v, w)

    def scalar(v):
        """Returns the scalar part of v"""
        return v[0]

    def vector(v):
        """Returns the vector part of v (as a Vec3)"""
        try:
            return v.__vector_part__
        except AttributeError:
            v.__vector_part__ = Vec3(v[1:])
            return v.__vector_part__

    inner = dot
    S = scalar
    V = vector

def transform3TypeStr(i):
    if i == Transform3.Rot: return 'Rot3'
    if i == Transform3.Refl: return 'Refl3'
    if i == Transform3.RotInv: return 'RotInv3'
    else: return 'Transform3'

def isQuatPair(q):
    return (
        q != None and
        len(q) == 2 and isinstance(q[0], Quat) and isinstance(q[1], Quat)
    )

class Transform3(tuple):
    debug = False
    def __new__(cls, quatPair):
        assertStr = "A 3D transform is represented by 2 quaternions: "
        assert len(quatPair) == 2, assertStr + str(quatPair)
        assert isinstance(quatPair[0], Quat), assertStr + str(quatPair)
        assert isinstance(quatPair[1], Quat), assertStr + str(quatPair)
        return tuple.__new__(cls, quatPair)

    def __repr__(self):
        s = indent.Str('%s((\n' % (transform3TypeStr(self.type())))
        s = s.add_incr_line('%s,' % repr(Quat(self[0])))
        s = s.add_line('%s,' % repr(Quat(self[1])))
        s = s.add_decr_line('))')
        if __name__ != '__main__':
            s = s.insert('%s.' % __name__)
        return s

    def __hash__(self):
        try:
            return self.__hash_nr__
        except AttributeError:
            if self.isRot(): self.__hash_nr__ = self.__hashRot__()
            elif self.isRefl(): self.__hash_nr__ = self.__hashRefl__()
            elif self.isRotInv(): self.__hash_nr__ = self.__hashRotInv__()
            else:
                raise TypeError, "Not a (supported) transform)"
            return self.__hash_nr__

    def __str__(self):
        if self.isRot(): return self.__strRot()
        elif self.isRefl(): return self.__strRefl()
        elif self.isRotInv(): return self.__strRotInv()
        else:
            return '%s * .. * %s' % (str(self[0]), str(self[1]))

    def to_orbit_str(self, prec=roundFloatMargin):
        if self.isRot(): return self.__rot2orbit(prec)
        elif self.isRefl(): return self.__refl2orbit(prec)
        elif self.isRotInv(): return self.__rotinv2orbit(prec)
        else: return "Unknown transform"

    def __mul__(self, u):
        if isinstance(u, Transform3):
            # self * u =  wLeft * vLeft .. vRight * wRight
            return Transform3([self[0] * u[0], u[1] * self[1]])
        # TODO: check kind of Transform3 and optimise
        elif isinstance(u, Vec) and len(u) == 3:
            return (self[0] * Quat([0, u[0], u[1], u[2]]) * self[1]).V()
        elif isinstance(u, Quat):
            return (self[0] * u                           * self[1]).V()
        else:
            return u.__rmul__(self)
            #raise TypeError, "unsupported op type(s) for *: '%s' and '%s'" % (
            #        self.__class__.__name__, u.__class__.__name__
            #    )

    def __eq__(self, u):
        if not isinstance(u, Transform3): return False
        if self.isRot() and u.isRot():
            #if self.__eqRot(u): print 'equal Rot:', self, u
            eq = self.__eqRot(u)
        elif self.isRefl() and u.isRefl():
            #if self.__eqRefl(u): print 'equal Refl:', self, u
            eq = self.__eqRefl(u)
        elif self.isRotInv() and u.isRotInv():
            #if self.__eqRotInv(u): print 'equal RotInv:', self, u
            eq = self.__eqRotInv(u)
        else:
            eq = self[0] == u[0] and self[1] == u[1]
            if eq: print 'fallback:', self[0], '==', u[0], 'and', self[1], '==', u[1]
            assert not eq, 'oops, fallback: unknown transform \n%s\nor\n%s' % (
                str(self), str(u))
            return eq
        if (eq and (self.__hash__() != u.__hash__())):
            print '\n*** warning hashing will not work between\n%s and\n%s' % (
                str(self), str(u)
            )
        return eq

    def __ne__(self, u):
        return not self == u

    Rot = 0
    Refl = 1
    RotInv = 2
    RotRefl = RotInv

    def type(self):
        if self.isRot(): return self.Rot
        if self.isRefl(): return self.Refl
        if self.isRotInv(): return self.RotInv
        raise TypeError, 'oops, unknown type of Transform: %s ?= 1' % (
            self[1].norm())

    def angle(self):
        if self.isRot(): return self.angleRot()
        if self.isRotInv(): return self.angleRotInv()
        raise TypeError, (
            'oops, unknown angle; transform %s\n' % str(self) +
            'neither a rotation, nor a rotary-inversion (-reflection)')

    def axis(self):
        if self.isRot(): return self.axisRot()
        if self.isRotInv(): return self.axisRotInv()
        raise TypeError, (
            'oops, unknown angle; transform %s\n' % str(self) +
            'neither a rotation, nor a rotary-inversion (-reflection)')

    def glMatrix(self):
        if self.isRot(): m = self.glMatrixRot()
        elif self.isRefl(): m = self.matrixRefl()
        elif self.isRotInv(): m = self.glMatrixRotInv()
        else: raise AssertionError
        return Mat([Vec([m[0][0], m[0][1], m[0][2], 0]),
                    Vec([m[1][0], m[1][1], m[1][2], 0]),
                    Vec([m[2][0], m[2][1], m[2][2], 0]),
                    Vec([0, 0, 0, 1])])

    def matrix(self):
        # TODO: test this
        if self.isRot(): return self.matrixRot()
        if self.isRefl(): return self.matrixRefl()
        if self.isRotInv(): return self.matrixRotInv()
        assert False, (
            'oops, unknown matrix; transform %s\n' % str(self) +
            'not a rotation')

#    def matrix4(self):
#        m = self.matrix()
#        return Mat([
#                Vec([m[0][0], m[0][1], m[0][2], 0]),
#                Vec([m[1][0], m[1][1], m[1][2], 0]),
#                Vec([m[2][0], m[2][1], m[2][2], 0]),
#                Vec([0,       0,       0,       1]),
#            ])

    def inverse(self):
        if self.isRot(): return self.inverseRot()
        if self.isRefl(): return self.inverseRefl()
        if self.isRotInv(): return self.inverseRotInv()
        assert False, (
            'oops, unknown matrix; transform %s\n' % str(self) +
            'not a rotation')

    def isDirect(self):
        return self.isRot()

    def isOpposite(self):
        return not self.isDirect()

    ## ROTATION specific functions:
    def isRot(self):
        global eqFloatMargin
        d = 1 - eqFloatMargin
        backup, eqFloatMargin = eqFloatMargin, 1 - d * d
        eqSquareNorm = eq(self[1].squareNorm(), 1)
        eqFloatMargin = backup
        #print (
        #        self[1].conjugate() == self[0]
        #        and
        #        eqSquareNorm
        #        and
        #        (self[1].S() < 1 or eq(self[1].S(), 1))
        #        and
        #        (self[1].S() > -1 or eq(self[1].S(), -1))
        #    ),
        #print 'isRot: %s..%s' % (str(self[0]), str(self[1]))
        #print  self[1].conjugate() == self[0], ': self[1].conjugate() == self[0]'
        #print '%s = self[1].conjugate() == self[0] %s ' % (
        #        self[1].conjugate(), self[0]
        #    )
        #print eq(self[1].squareNorm(), 1),
        #print '    1 ?= self[1].norm() = %0.17f' % self[1].squareNorm(),
        #print  '(d =', 1 - self[1].squareNorm(), '>', eqFloatMargin, ')'
        #print (
        #        (self[1].S() < 1 or eq(self[1].S(), 1))
        #        and
        #        (self[1].S() > -1 or eq(self[1].S(), -1))
        #    ), ':'
        #print '   -1 ?<= self.S() = %0.17f ?<= 1' % self[1].S()
        return (
            self[1].conjugate() == self[0]
            and
            eqSquareNorm
            and
            (self[1].S() < 1 or eq(self[1].S(), 1))
            and
            (self[1].S() > -1 or eq(self[1].S(), -1))
        )

    def __eqRot(self, u):
        """Compare two transforms that represent rotations
        """
        #print '__eqRot'
        #print '%s ?= %s' % (str(self[0]), str(u[0]))
        #print '%s ?= %s' % (str(self[1]), str(u[1]))
        return (
            (self[0] == u[0] and self[1] == u[1])
            or
            # negative axis with negative angle:
            (self[0] == -u[0] and self[1] == -u[1])
            or
            # half turn (equal angle) around opposite axes
            (eq(self[0][0], 0) and self[0] == u[1])
        )

    def __hashRot__(self):
        axis = self.axisRot()
        return hash((self.Rot,
                     round(self.angleRot(), roundFloatMargin),
                     round(axis[0], roundFloatMargin),
                     round(axis[1], roundFloatMargin),
                     round(axis[2], roundFloatMargin)))

    def __strRot(self):
        axis = self.axisRot()
        return 'Rotation of {} degrees around [{}, {}, {}]'.format(
            float2str(degrees(self.angleRot()), roundFloatMargin),
            float2str(axis[0], roundFloatMargin),
            float2str(axis[1], roundFloatMargin),
            float2str(axis[2], roundFloatMargin))

    def __rot2orbit(self, prec=roundFloatMargin):
        axis = self.axisRot()
        return 'R {} {} {} {}'.format(
            float2str(self.angleRot(), prec),
            float2str(axis[0], prec),
            float2str(axis[1], prec),
            float2str(axis[2], prec))

    def angleRot(self):
        try:
            return self.__angleRot__
        except AttributeError:
            self.defUniqueAngleAxis()
            return self.__angleRot__

    def axisRot(self):
        try:
            return self.__axisRot__
        except AttributeError:
            self.defUniqueAngleAxis()
            return self.__axisRot__

    def defUniqueAngleAxis(self):
        # rotation axis
        try:
            self.__axisRot__ = self[0].V().normalise()
        except ZeroDivisionError:
            assert self[0] == Quat([1, 0, 0, 0]) or \
                self[0] == Quat([-1, 0, 0, 0]), \
                "{} doesn'self represent a rotation".format(self.__repr__())
            self.__axisRot__ = self[0].V()
        # rotation angle
        cos = self[0][0]
        for i in range(3):
            try:
                sin = self[0][i+1] / self[0].V().normalise()[i]
                break
            except ZeroDivisionError:
                if i == 2:
                    assert self[0] == Quat([1, 0, 0, 0]) or \
                        self[0] == Quat([-1, 0, 0, 0]), \
                        "{} doesn'self represent a rotation".format(
                            self.__repr__())
                    sin = 0
        #print 'reconstructed cos =', cos
        #print 'reconstructed sin =', sin
        self.__angleRot__ = 2 * math.atan2(sin, cos)

        # make unique: -pi < angle < pi
        if not (self.__angleRot__ < math.pi or eq(self.__angleRot__, math.pi)):
            self.__angleRot__ = self.__angleRot__ - 2 * math.pi
        if not (self.__angleRot__ > -math.pi or eq(self.__angleRot__, -math.pi)):
            self.__angleRot__ = self.__angleRot__ + 2 * math.pi

        # make unique: 0 < angle < pi
        if eq(self.__angleRot__, 0):
            self.__angleRot__ = 0.0
        if self.__angleRot__ < 0:
            self.__angleRot__ = -self.__angleRot__
            self.__axisRot__ = -self.__axisRot__
        if eq(self.__angleRot__, math.pi):
            # if halfturn, make axis unique: make the first non-zero element
            # positive:
            if eq(self.__axisRot__[0], 0):
                self.__axisRot__ = Vec3([0.0,
                                         self.__axisRot__[1],
                                         self.__axisRot__[2]])
            if self.__axisRot__[0] < 0:
                self.__axisRot__ = -self.__axisRot__
            elif self.__axisRot__[0] == 0:
                if eq(self.__axisRot__[1], 0):
                    self.__axisRot__ = Vec3([0.0, 0.0, self.__axisRot__[2]])
                if self.__axisRot__[1] < 0:
                    self.__axisRot__ = -self.__axisRot__
                elif self.__axisRot__[1] == 0:
                    # not valid axis: if eq(self.__axisRot__[2], 0):
                    if self.__axisRot__[2] < 0:
                        self.__axisRot__ = -self.__axisRot__
        elif eq(self.__angleRot__, 0):
            self.__angleRot__ = 0.0
            self.__axisRot__ = Vec3([1.0, 0.0, 0.0])

    def getMatrixRot(self, w, x, y, z, sign=1):
        dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
        dxw, dyw, dzw = 2*x*w, 2*y*w, 2*z*w
        dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
        return [
            Vec([sign*(1-dy2-dz2), sign*(dxy-dzw), sign*(dxz+dyw)]),
            Vec([sign*(dxy+dzw), sign*(1-dx2-dz2), sign*(dyz-dxw)]),
            Vec([sign*(dxz-dyw), sign*(dyz+dxw), sign*(1-dx2-dy2)])]

    def matrixRot(self):
        try:
            return self.__matrix_rot__
        except AttributeError:
            w, x, y, z = self[0]
            self.__matrix_rot__ = self.getMatrixRot(w, x, y, z)
            return self.__matrix_rot__

    def glMatrixRot(self):
        try:
            return self.__gl_matrix_rot__
        except AttributeError:
            w, x, y, z = self[0]
            self.__gl_matrix_rot__ = self.getMatrixRot(-w, x, y, z)
            return self.__gl_matrix_rot__

    def inverseRot(self):
        try:
            return self.__inverse_rot__
        except AttributeError:
            self.__inverse_rot__ = Rot3(axis=self.axis(), angle=-self.angle())
            return self.__inverse_rot__

    ## REFLECTION specific functions:
    def isRefl(self):
        #print 'self[1] == self[0]:', self[1] == self[0]
        #print '1 ?= self[1].norm() = %0.17f' % self[1].norm()
        #print '0 ?= self[1].S() = %0.17f' % self[1].S()
        return (
            self[1] == self[0]
            and
            eq(self[1].squareNorm(), 1)
            and
            eq(self[1].S(), 0)
        )

    def __eqRefl(self, u):
        """Compare two transforms that represent reflections"""
        # not needed: and self[1] == u[1]
        # since __eqRefl is called for self and u reflections
        return (self[0] == u[0]) or (self[0] == -u[0])

    def __hashRefl__(self):
        normal = self.planeN()
        return hash(
            (
                self.Refl,
                self.Refl, # to use a tuple of 5 elements for all types
                round(normal[0], roundFloatMargin),
                round(normal[1], roundFloatMargin),
                round(normal[2], roundFloatMargin)
            )
        )

    def __strRefl(self):
        norm = self.planeN()
        return 'Reflection in plane with normal [{}, {}, {}]'.format(
            float2str(norm[0], roundFloatMargin),
            float2str(norm[1], roundFloatMargin),
            float2str(norm[2], roundFloatMargin))

    def __refl2orbit(self, prec=roundFloatMargin):
        norm = self.planeN()
        return 'S {} {} {}'.format(
            float2str(norm[0], prec),
            float2str(norm[1], prec),
            float2str(norm[2], prec))

    def planeN(self):
        try:
            return self.__plane_normal__
        except AttributeError:
            self.__plane_normal__ = self[0].V()
            # make normal unique: make the first non-zero element positive:
            if eq(self.__plane_normal__[0], 0):
                self.__plane_normal__ = Vec3(
                    [0.0, self.__plane_normal__[1], self.__plane_normal__[2]])
            if self.__plane_normal__[0] < 0:
                self.__plane_normal__ = -self.__plane_normal__
            elif self.__plane_normal__[0] == 0:
                if eq(self.__plane_normal__[1], 0):
                    self.__plane_normal__ = Vec3([0.0,
                                                  0.0,
                                                  self.__plane_normal__[2]])
                if self.__plane_normal__[1] < 0:
                    self.__plane_normal__ = -self.__plane_normal__
                elif self.__plane_normal__[1] == 0:
                    # not valid axis: if eq(self.__plane_normal__[2], 0):
                    if self.__plane_normal__[2] < 0:
                        self.__plane_normal__ = -self.__plane_normal__
            return self.__plane_normal__

    def matrixRefl(self):
        try:
            return self.__matrix_refl__
        except AttributeError:
            w, x, y, z = self[0]
            dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
            dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
            self.__matrix_refl__ = [
                Vec([1-dx2, -dxy, -dxz]),
                Vec([-dxy, 1-dy2, -dyz]),
                Vec([-dxz, -dyz, 1-dz2]),
            ]
            return self.__matrix_refl__

    def inverseRefl(self):
        return self

    ## ROTARY INVERSION (= ROTARY RELECTION) specific functions:
    def I(self):
        """
        Apply a central inversion
        """
        try:
            return self.__central_inverted__
        except AttributeError:
            self.__central_inverted__ = Transform3([-self[0], self[1]])
            return self.__central_inverted__

    def isRotInv(self):
        return self.I().isRot() and not self.isRefl()

    def __eqRotInv(self, u):
        return self.I().__eqRot(u.I())

    def __hashRotInv__(self):
        axis = self.axisRotInv()
        return hash((self.Rot,
                     round(self.angleRotInv(), roundFloatMargin),
                     round(axis[0], roundFloatMargin),
                     round(axis[1], roundFloatMargin),
                     round(axis[2], roundFloatMargin)))

    def __strRotInv(self):
        r = self.I()
        axis = r.axisRot()
        return 'Rotary inversion of {} degrees around [{}, {}, {}]'.format(
            float2str(degrees(r.angleRot()), roundFloatMargin),
            float2str(axis[0], roundFloatMargin),
            float2str(axis[1], roundFloatMargin),
            float2str(axis[2], roundFloatMargin))
        return str

    def __rotinv2orbit(self, prec=roundFloatMargin):
        r = self.I()
        return 'I' + r.__rot2orbit(prec)[1:]

    def angleRotInv(self):
        return self.I().angleRot()

    def axisRotInv(self):
        return self.I().axisRot()

    def matrixRotInv(self):
        try:
            return self.__matrix_rot_inv__
        except AttributeError:
            w, x, y, z = self[0]
            self.__matrix_rot_inv__ = self.getMatrixRot(w, x, y, z, -1)
            return self.__matrix_rot_inv__

    def glMatrixRotInv(self):
        try:
            return self.__gl_matrix_rot_inv__
        except AttributeError:
            w, x, y, z = self[0]
            self.__gl_matrix_rot_inv__ = self.getMatrixRot(-w, x, y, z, -1)
            return self.__gl_matrix_rot_inv__

    def inverseRotInv(self):
        try:
            return self.__inverse_rot_inv__
        except AttributeError:
            self.__inverse_rot_inv__ = RotInv3(axis=self.axis(),
                                               angle=-self.angle())
            return self.__inverse_rot_inv__

        isRotRefl = isRotInv
        axisRotRefl = axisRotInv

    def angleRotRefl(self):
        return self.angleRotInv() - hTurn

class Rot3(Transform3):
    def __new__(cls, q=None, axis=Vec3([1, 0, 0]), angle=0):
        """
        Initialise a 3D rotation
        axis: axis to rotate around: doesn't need to be normalised
        angle: angle in radians to rotate
        """
        if isQuatPair(q):
            t = Transform3.__new__(cls, q)
            assert t.isRot(), "%s doesn't represent a rotation" % str(q)
            return t
        elif isinstance(q, Quat):
            try:
                q = q.normalise()
            except ZeroDivisionError:
                pass # will fail on assert below:
            t = Transform3.__new__(cls, [q, q.conjugate()])
            assert t.isRot(), "%s doesn't represent a rotation" % str(q)
            return t
        else:
            # q = cos(angle) + y sin(angle)
            alpha = angle / 2
            # if axis is specified as e.g. a list:
            if not isinstance(axis, Vec):
                axis = Vec3(axis)
            if axis != Vec3([0, 0, 0]):
                axis = axis.normalise()
            q = math.sin(alpha) * axis
            q = Quat([math.cos(alpha), q[0], q[1], q[2]])
            #print 'cos =', math.cos(alpha)
            #print 'sin =', math.sin(alpha)
            return Transform3.__new__(cls, [q, q.conjugate()])

class HalfTurn3(Rot3):
    def __new__(cls, axis):
        return Rot3.__new__(cls, axis=axis, angle=hTurn)

class Rotx(Rot3):
    def __init__(cls, angle):
        return Rot3.__new__(cls, axis=ux, angle=angle)

class Roty(Rot3):
    def __new__(cls, angle):
        return Rot3.__new__(cls, axis=uy, angle=angle)

class Rotz(Rot3):
    def __new__(cls, angle):
        return Rot3.__new__(cls, axis=uz, angle=angle)

class Refl3(Transform3):
    def __new__(cls, q=None, planeN=None):
        """Define a 3D reflection is a plane

        Either define
        q: quaternion representing the left (and right) quaternion
        multiplication for a reflection
        or
        planeN: the 3D normal of the plane in which the reflection takes place.
        """
        result = None
        if isQuatPair(q):
            result = Transform3.__new__(cls, q)
            assert result.isRefl(), "%s doesn't represent a reflection" % str(q)
        elif isinstance(q, Quat):
            try:
                q = q.normalise()
            except ZeroDivisionError:
                pass # will fail on assert below:
            result = Transform3.__new__(cls, [q, q])
            assert result.isRefl(), "%s doesn't represent a reflection" % str(q)
        else:
            try:
                normal = planeN.normalise()
                q = Quat(normal)
            except ZeroDivisionError:
                q = Quat(planeN) # will fail on assert below:
            result = Transform3.__new__(cls, [q, q])
            assert result.isRefl(), (
                "normal %s doesn't define a valid 3D plane normal" % str(planeN)
            )
        return result

class RotInv3(Transform3):
    def __new__(cls, qLeft=None, axis=None, angle=None):
        """
        Initialise a 3D rotation
        """
        # Do not inherit from Rot3 (and then apply inversion):
        # a rotary inversion is not a rotation.
        result = None
        if isQuatPair(qLeft):
            result = Transform3.__new__(cls, qLeft)
            assert result.isRotInv(), "%s doesn't represent a rotary inversion" % (
                str(qLeft))
        else:
            ri = Rot3(qLeft, axis, angle).I()
            result = Transform3.__new__(cls, [ri[0], ri[1]])
        return result

RotRefl = RotInv3
Hx = HalfTurn3(ux)
Hy = HalfTurn3(uy)
Hz = HalfTurn3(uz)
I = RotInv3(Quat([1, 0, 0, 0]))
E = Rot3(Quat([1, 0, 0, 0]))

# TODO: make the 3D case a special case of 4D...
class Transform4(tuple):
    def __new__(cls, quatPair):
        assertStr = "A 4D transform is represented by 2 quaternions: "
        assert len(quatPair) == 2, assertStr + str(quatPair)
        assert isinstance(quatPair[0], Quat), assertStr + str(quatPair)
        assert isinstance(quatPair[1], Quat), assertStr + str(quatPair)
        return tuple.__new__(cls, quatPair)

    def __mul__(self, u):
        if isinstance(u, (Transform3, Transform4)):
            # self * u =  wLeft * vLeft .. vRight * wRight
            return Transform4([self[0] * u[0], u[1] * self[1]])
        # TODO: check kind of Transform4 and optimise
        if isinstance(u, Vec) and len(u) == 3:
            return self[0] * Quat([0, u[0], u[1], u[2]]) * self[1]
        if isinstance(u, Quat):
            return self[0] * u * self[1]
        if isinstance(u, Vec) and len(u) == 4:
            return self[0] * Quat(u) * self[1]
        return u.__rmul__(self)
        #raise TypeError, "unsupported op type(s) for *: '%s' and '%s'" % (
        #        self.__class__.__name__, u.__class__.__name__
        #    )

    def angle(self):
        if self.isRot():
            return self.angleRot()
        #if self.isRotInv(): return self.angleRotInv()
        assert False, (
            'oops, unknown angle; transform {}\n'.format(str(self)) +
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )
        return None

    def isRot(self):
        # print 't0', self[0].squareNorm() - 1
        # print 't1', self[1].squareNorm() - 1
        return eq(self[0].squareNorm(), 1) and eq(self[1].squareNorm(), 1)

    def angleRot(self):
        cos = self[0][0]
        for i in range(3):
            try:
                sin = self[0][i+1] / self[0].V().normalise()[i]
                break
            except ZeroDivisionError:
                if i == 2:
                    assert self[0] == Quat([1, 0, 0, 0]) or \
                        self[0] == Quat([-1, 0, 0, 0]), \
                        "{} doesn't represent a rotation".format(
                            self.__repr__())
                    return 0
        #print 'reconstructed cos =', cos
        #print 'reconstructed sin =', sin
        return 2 * math.atan2(sin, cos)

class Rot4(Transform4):
    def __new__(cls,
                quatPair=None,
                axialPlane=(Vec4([0, 0, 1, 0]), Vec4([0, 0, 0, 1])),
                angle=0):
        """
        Initialise a 4D rotation
        """
        assertStr = "A 4D rotation is represented by 2 orthogonal axis: "
        assert len(axialPlane) == 2, assertStr + str(axialPlane)
        assert eq(axialPlane[0] * axialPlane[1], 0), \
            assertStr + str(axialPlane)
        # Do not require Quats for the axial plane: this is a implementation
        # choice, which should be abstracted from.
        axialPlane = (Quat(axialPlane[0]), Quat(axialPlane[1]))
        # Coxeter Regular Complex Polytopes, p 71
        #                  _
        # qleft  = cosa + yz sina
        #                 _
        # qright = cosa + yz sina
        #
        # Note:                       _        _
        # Since y and z orthogonal: S(yz) = S(yz) == 0
        y = axialPlane[0].normalise()
        z = axialPlane[1].normalise()
        q0 = y             * z.conjugate()
        q1 = y.conjugate() * z
        assert eq(q0.scalar(), 0), assertStr + str(q0.scalar())
        assert eq(q1.scalar(), 0), assertStr + str(q1.scalar())
        alpha = angle / 2
        sina = math.sin(alpha)
        cosa = math.cos(alpha)
        q0 = sina * q0.vector()
        q1 = sina * q1.vector()
        return Transform4.__new__(cls,
                                    [Quat([cosa, q0[0], q0[1], q0[2]]),
                                    Quat([cosa, q1[0], q1[1], q1[2]])])

def findOrthoPlane(plane):
    """From the defined 4D plane, find the orthogonal plane"""
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
    def getZeroIndex(v, s=0):
        """
        Get the index of the element that equals to 0 in vec v. If there
        none, -1 is returned.

        s: start with (incl) position s
        """
        zeroIndex = -1
        #print 'getZeroIndex', v, s
        for i in range(s, 4):
            if eq(v[i], 0):
                zeroIndex = i
                break
        return zeroIndex

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
    status = {'sz_e0': -1, 'sz_e1': -1, 'e0_z_e1': 0, 'sp': 0}

    # define e0 and e1 locally to be able to exchange their roll just for
    # calculating e2 and e3.
    e0 = plane[0].normalise()
    e1 = plane[1].normalise()

    # Now define e2,..
    zi = getZeroIndex(e0)
    if zi > -1: # if e0 contains a 0 (zero)
        v2 = unitVec4(zi)
        if v2.isParallel(e1):
            # exchange e0 and e1 and repeat, since we know that e1 has 3 0's
            e0, e1 = e1, e0
            status['e0_z_e1'] = 1
            zi = getZeroIndex(e0)
            if zi > -1:
                v2 = unitVec4(zi)
                if v2.isParallel(e1):
                    # ok, e0 had 3 zeros as well,...
                    zi = getZeroIndex(e0, zi+1)
                    if zi > -1:
                        v2 = unitVec4(zi)
                        assert not v2.isParallel(e1), oopsMsg
                    else:
                        assert False, oopsMsg
            else:
                assert False, oopsMsg
        status['sz_e0'] = zi
    else:
        status['sz_e0'] = 3
        zi = getZeroIndex(e1)
        if zi > -1:  # if e1 contains a 0 (zero)
            v2 = unitVec4(zi)
            e0, e1 = e1, e0
            status['e0_z_e1'] = 2
            assert not v2.isParallel(e1), "Ooops, this shouldn't happen!!"
            status['sz_e1'] = zi
        else:
            vnIni = Vec4([1/e0[0], 1/e0[1], 1/e0[2], 1/e0[3]])
            possiblePermuations = [
                Vec4([vnIni[0], vnIni[1], -vnIni[2], -vnIni[3]]),
                Vec4([vnIni[0], -vnIni[1], vnIni[2], -vnIni[3]]),
                Vec4([-vnIni[0], vnIni[1], vnIni[2], -vnIni[3]]),
                # this might be used later for e3:
                Vec4([vnIni[0], -vnIni[1], -vnIni[2], vnIni[3]]),
                # I don't think these are necessary:
                #Vec4([-vnIni[0],  vnIni[1], -vnIni[2],  vnIni[3]]),
                #Vec4([-vnIni[0], -vnIni[1],  vnIni[2],  vnIni[3]])
            ]
            v2Found = False
            i = -1
            while not v2Found:
                i += 1
                assert i < len(possiblePermuations), "Oops, more permutations needed"
                v2 = possiblePermuations[i]
                v2Found = not v2.isParallel(e1)
            status['sp'] = i + 1

    # Now the plane spanned by e1 and v2 is orthogonal to e0, as a
    # consequence the following operation will keep v2 orthogonal to e0:
    e2 = v2.makeOrthogonalTo(e1).normalise()

    # Use cross product for e3:
    v3 = e0.cross(e1, e2)
    # Normalisation should not be needed, but improves precision.
    #print '__findOrthoPlane: v3', v3
    # TODO
    # Prehaps this should only steered by caller by setting high precision.
    e3 = v3.normalise()
    #print 'e3', self.e3
    return (e2, e3)

class DoubleRot4(Transform4):
    """Define the general (double) rotation in 4D"""
    def __new__(cls,
                quatPair=None,
                axialPlane=(Vec4([0, 0, 1, 0]), Vec4([0, 0, 0, 1])),
                angle=(0, 0)):
        orthoPlane = findOrthoPlane(axialPlane)
        r0 = Rot4(axialPlane=axialPlane, angle=angle[0])
        r1 = Rot4(axialPlane=orthoPlane, angle=angle[1])
        return Transform4.__new__(cls, [r1[0]*r0[0], r0[1]*r1[1]])

# TODO implement Geom3D.Line3D here (in this file)

# forced to use some matrix functions and don't want to add a dependency on a
# big python package.

class Mat(list):
    """Contruct matrix"""
    def __init__(self, m=None, dim=3):
        """Initialise matrix as m or as unit with dimension dimxdim"""
        if m is None:
            m = []
            assert dim > 0
            for i in range(dim):
                v = []
                for j in range(dim):
                    if i == j:
                        v.append(1)
                    else: v.append(0)
                m.append(Vec(v))
        self.rows = len(m)
        assert self.rows > 0
        self.cols = len(m[0])
        for row in m:
            assert isinstance(row, Vec)
            assert len(row) == self.cols
        list.__init__(self, m)

    def __str__(self):
        """Human readable string representation"""
        s = ''
        for row in self:
            s = '%s\n%s' % (s, str(row))
        return s

    def row(self, i):
        """Return row 'i'"""
        return self[i]

    def col(self, i):
        """Return column 'i'"""
        return Vec([row[i] for row in self])

    def transpose(self):
        """Return transpose of matrix"""
        return Mat([self.col(i) for i in range(self.cols)])

    T = transpose

    def deleteRow(self, i):
        """Delete row i"""
        # don't use self.pop(i), it changes self, while the result should be
        # returned instead.
        if i < 0:
            i += self.rows
        assert i >= 0
        n = self[0:i]
        n.extend(self[i+1:])
        return Mat(n)

    def deleteCol(self, i):
        """Delete column i"""
        if i < 0:
            i += self.cols
        assert i >= 0
        n = []
        for row in self:
            r = list(row[0:i])
            r.extend(list(row[i+1:]))
            n.append(Vec(r))
        return Mat(n)

    def replaceCol(self, i, v):
        """Replace column i with vector v"""
        assert len(v) == self.rows
        if i < 0:
            i += self.cols
        assert i >= 0
        n = []
        for k, row in zip(range(self.rows), self):
            r = list(row[0:i])
            r.append(v[k])
            r.extend(list(row[i+1:]))
            n.append(Vec(r))
        return Mat(n)

    def minor(self, i, j):
        """Return minor matrix by deleting row i and column j"""
        return self.deleteRow(i).deleteCol(j).det()

    def orthogonal(self):
        """Check whether this is an orthogonal matrix"""
        return abs(self.det()) == 1

    def det(self):
        """Determinant of matrix"""
        assert self.rows == self.cols
        if self.rows == 2:
            return self[0][0] * self[1][1] - self[0][1]*self[1][0]
        if self.rows == 1:
            return self[0][0]
        #else:
        r = 0
        sign = 1
        for i in range(self.cols):
            if not eq(self[0][i], 0):
                r += sign * self[0][i] * self.minor(0, i)
            sign = -sign
        return r

    def __mul__(self, n):
        """Mulitply matrix with matrix / vector"""
        result = None
        if isinstance(n, Mat):
            assert self.rows == n.cols
            assert n.rows == self.cols
            nT = n.T()
            result = Mat([Vec([row * col for col in nT]) for row in self])
        elif isinstance(n, Vec):
            assert self.rows == len(n)
            result = Vec([row * n for row in self])
        else:
            assert False, \
                'unknown type of object to multiply matrix: {}.'.format(n)
        return result

    def inverse(self):
        """Return inverse matrix"""
        if self.orthogonal():
            return self.T()
        else:
            # the hard way:
            det = self.det()
            sign = 1
            n = []
            for i in range(self.rows):
                r = []
                for j in range(self.cols):
                    r.append(sign * self.minor(i, j) / det)
                    sign = -sign
                n.append(Vec(r))
        return Mat(n).T()

    def solve(self, v):
        """Solve matrix usinguse Cramer's method"""
        assert len(v) == self.rows
        det = self.det()
        return Vec(
            [self.replaceCol(i, v).det() / det for i in range(self.cols)])

    def stdRowShape(self, v):
        """Not implemented: put matrix in standard row shape"""
        pass

if __name__ == '__main__':
    from random import seed, random

    #####################
    # Vec
    #####################
    R = Vec([])
    assert R == [], 'got %s instead' % str(R)

    V = Vec([1, 2, 4])
    W = Vec([2, 3, 5, 6])

    R = -V
    assert R == Vec([-1.0, -2.0, -4.0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    R = V+W
    assert R == Vec([3.0, 5.0, 9.0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    R = W-V
    assert R == Vec([1.0, 1.0, 1.0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    R = V*2
    assert R == Vec([2.0, 4.0, 8.0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    R = 2*V
    assert R == Vec([2.0, 4.0, 8.0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    R = V/2
    assert R == Vec([0.5, 1.0, 2.0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    #V[1] = 5.0
    #assert V == Vec([1.0, 5.0, 4.0]), 'got %s instead' % V
    #assert type(V) == type(Vec([]))

    V = Vec([1.0, 5.0, 4.0])
    R = V[1:]
    assert R == Vec([5.0, 4.0]), 'got %s instead' % str(R)
    # TODO: howto without using deprecated __setslice__ ?
    # currently no problem, since R + W becomes a Vec anyway,
    # though 3 * R gives unexpected result
    #assert type(R) == type(Vec([]))

    V = Vec([1, 2, 4])
    R = V.norm()
    assert R == math.sqrt(1+4+16), 'got %s instead' % str(R)

    V = Vec([3, 4, 5])
    N = V.norm()
    R = V.normalize()
    assert R == Vec([V[0]/N, V[1]/N, V[2]/N]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    R = V.normalise()
    assert R == Vec([V[0]/N, V[1]/N, V[2]/N]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    V = Vec([0, 0, 0])
    W = Vec([10, 0, 0])
    try:
        R = V.angle(W)
        assert False, 'exptected ZeroDivisionError: got %s instead' % str(R)
    except ZeroDivisionError:
        pass

    V = Vec([10, 0, 0])
    W = Vec([0, 0, 0])
    try:
        R = V.angle(W)
        assert False, 'exptected ZeroDivisionError: got %s instead' % str(R)
    except ZeroDivisionError:
        pass

    V = Vec([0, 0, 0])
    W = Vec([0, 0, 0])
    try:
        R = V.angle(W)
        assert False, 'exptected ZeroDivisionError: got %s instead' % str(R)
    except ZeroDivisionError:
        pass

    V = Vec([4, 0, 0])
    W = Vec([10, 0, 0])
    R = V.angle(W)
    assert R == 0, 'got %s instead' % str(R)

    V = Vec([10, 0, 0])
    W = Vec([0, 3, 0])
    R = V.angle(W)
    assert R == qTurn, 'got %s instead' % str(R)

    V = Vec([0, 10, 0])
    W = Vec([0, 3, 3])
    R = V.angle(W)
    assert R == math.pi/4, 'got %s instead' % str(R)

    V = Vec([0, 10, 0])
    W = Vec([0, -3, 0])
    R = V.angle(W)
    assert R == hTurn, 'got %s instead' % str(R)

    # Vec3
    V = Vec3([1, 2, 3])
    W = Vec3([2, -3, 4])
    R = V.cross(W)
    assert R == Vec3([17, 2, -7]), 'got %s instead' % str(R)
    assert isinstance(R, Vec3)

    V = Vec3([1, 0, 0])
    W = Vec3([1, 0, 0])
    R = V.cross(W)
    assert R == Vec3([0, 0, 0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec3)

    V = Vec3([0, 0, 0])
    W = Vec3([1, 0, 0])
    R = V.cross(W)
    assert R == Vec3([0, 0, 0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec3)

    V = Vec3([1, 0, 0])
    W = Vec3([0, 0, 0])
    R = V.cross(W)
    assert R == Vec3([0, 0, 0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec3)

    V = Vec3([0, 0, 0])
    W = Vec3([0, 0, 0])
    R = V.cross(W)
    assert R == Vec3([0, 0, 0]), 'got %s instead' % str(R)
    assert isinstance(R, Vec3)

    #####################
    # Quat
    #####################
    q0 = Quat([1, 2, 3, 5])
    q1 = Quat([2, 4, 3, 5])
    R = q0 * q1
    assert R == Quat([-40, 8, 19, 9]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    q0 = Quat([0, 0, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    R = q0 * q1
    assert R == Quat([0, 0, 0, 0]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    q0 = Quat([1, 0, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    R = q0 * q1
    assert R == Quat([2, 4, 3, 5]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    q0 = Quat([0, 1, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    R = q0 * q1
    assert R == Quat([-4, 2, -5, 3]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    q0 = Quat([0, 0, 1, 0])
    q1 = Quat([2, 4, 3, 5])
    R = q0 * q1
    assert R == Quat([-3, 5, 2, -4]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    q0 = Quat([0, 0, 0, 1])
    q1 = Quat([2, 4, 3, 5])
    R = q0 * q1
    assert R == Quat([-5, -3, 4, 2]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    q = Quat([2, 4, 3, 5])
    R = q.S()
    assert R == 2, 'got %s instead' % str(R)
    assert isinstance(R, float)
    R = q.V()
    assert R == Vec3([4, 3, 5]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    q = Quat([2, 4, 3, 5])
    R = q.conjugate()
    assert R == Quat([2, -4, -3, -5]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    q = Quat([2, 0, 0, 5])
    R = q.conjugate()
    assert R == Quat([2, 0, 0, -5]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    q = Quat([0, 0, 0, 0])
    R = q.conjugate()
    assert R == q, 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    #####################
    # Transform: Rot3
    #####################

    R = I * I
    assert I != E, "This shouldn't hold %s != %s" % (I, E)
    assert R == E, 'got %s instead' % str(R)

    q0 = Rot3(axis=uz, angle=0)
    q1 = Rot3(axis=uz, angle=2*math.pi)
    assert q0 == q1, "%s should = %s" % (str(q0), str(q1))

    q0 = Rot3(axis=uz, angle=math.pi)
    q1 = Rot3(axis=uz, angle=-math.pi)
    assert q0 == q1, "%s should = %s" % (str(q0), str(q1))

    R = Rot3(axis=Vec3([0, 0, 0]), angle=0)
    assert R[1] == Quat([1, 0, 0, 0]), 'got %s instead' % R[1]
    assert R[0] == Quat([1, 0, 0, 0]), 'got %s instead' % R[0]

    #for a, b, in zip(R[1], Quat([1, 0, 0, 0])):
    #    print '%0.15f' % (a - b)

    # rotation around z -axis
    # 0 degrees (+/- 360)
    q = Rot3(axis=uz, angle=0)
    V = Vec3(ux)
    R = q*V
    assert R == ux, 'got %s instead' % str(R)

    # same as above but specifying the axis as a list
    q = Rot3(axis=[0, 0, 1], angle=0)
    V = Vec3(ux)
    R = q*V
    assert R == ux, 'got %s instead' % str(R)

    q = Rot3(axis=uz, angle=fullTurn)
    V = Vec3(ux)
    R = q*V
    assert R == ux, 'got %s instead' % str(R)

    q = Rot3(axis=uz, angle=-fullTurn)
    V = Vec3(ux)
    R = q*V
    assert R == ux, 'got %s instead' % str(R)

    # 90 degrees (+/- 360)
    q = Rot3(axis=uz, angle=qTurn)
    V = Vec3(ux)
    R = q*V
    assert R == uy, 'got %s instead' % str(R)

    q = Rot3(axis=uz, angle=qTurn + fullTurn)
    V = Vec3(ux)
    R = q*V
    assert R == uy, 'got %s instead' % str(R)

    q = Rot3(axis=uz, angle=qTurn - fullTurn)
    V = Vec3(ux)
    R = q*V
    assert R == uy, 'got %s instead' % str(R)

    # 180 degrees (+/- 360)
    q = Rot3(axis=uz, angle=hTurn)
    V = Vec3(ux)
    R = q*V
    assert R == -ux, 'got %s instead' % str(R)

    q = Rot3(axis=uz, angle=hTurn + fullTurn)
    V = Vec3(ux)
    R = q*V
    assert R == -ux, 'got %s instead' % str(R)

    q = Rot3(axis=uz, angle=hTurn - fullTurn)
    V = Vec3(ux)
    R = q*V
    assert R == -ux, 'got %s instead' % str(R)

    # -90 degrees (+/- 360)
    q = Rot3(axis=uz, angle=-qTurn)
    V = Vec3(ux)
    R = q*V
    assert R == -uy, 'got %s instead' % str(R)

    q = Rot3(axis=uz, angle=-qTurn + fullTurn)
    V = Vec3(ux)
    R = q*V
    assert R == -uy, 'got %s instead' % str(R)

    q = Rot3(axis=uz, angle=-qTurn - fullTurn)
    V = Vec3(ux)
    R = q*V
    assert R == -uy, 'got %s instead' % str(R)

    # Quadrant I
    hV3 = math.sqrt(3) / 2
    q = Rot3(axis=uz, angle=math.pi/3)
    V = ux + 3*uz
    R = q*V
    assert R == Vec3([0.5, hV3, 3]), 'got %s instead' % str(R)

    # Quadrant II
    q = Rot3(axis=uz, angle=hTurn - math.pi/3)
    V = ux + 3*uz
    R = q*V
    assert R == Vec3([-0.5, hV3, 3]), 'got %s instead' % str(R)

    # Quadrant III
    q = Rot3(axis=uz, angle=math.pi + math.pi/3)
    V = ux + 3*uz
    R = q*V
    assert R == Vec3([-0.5, -hV3, 3]), 'got %s instead' % str(R)

    # Quadrant IV
    q = Rot3(axis=uz, angle=- math.pi/3)
    V = ux + 3*uz
    R = q*V
    assert R == Vec3([0.5, -hV3, 3]), 'got %s instead' % str(R)

    # 3D Quadrant I: rotation around (1, 1, 1): don't specify normalise axis
    q = Rot3(axis=Vec3([1, 1, 1]), angle=tTurn)
    V = Vec3([-1, 1, 1])
    R = q*V
    assert R == Vec3([1, -1, 1]), 'got %s instead' % str(R)
    # neg angle
    q = Rot3(axis=Vec3([1, 1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([1, 1, -1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    q = Rot3(axis=-Vec3([1, 1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([1, -1, 1]), 'got %s instead' % str(R)
    # neg axis
    q = Rot3(axis=-Vec3([1, 1, 1]), angle=tTurn)
    R = q*V
    assert R == Vec3([1, 1, -1]), 'got %s instead' % str(R)

    # 3D Quadrant II: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis=Vec3([-1, 1, 1]), angle=tTurn)
    V = Vec3([1, 1, 1])
    R = q*V
    assert R == Vec3([-1, 1, -1]), 'got %s instead' % str(R)
    # neg angle
    q = Rot3(axis=Vec3([-1, 1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    q = Rot3(axis=-Vec3([-1, 1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([-1, 1, -1]), 'got %s instead' % str(R)
    # neg axis
    q = Rot3(axis=-Vec3([-1, 1, 1]), angle=tTurn)
    R = q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)

    # 3D Quadrant III: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis=Vec3([-1, -1, 1]), angle=tTurn)
    V = Vec3([1, 1, 1])
    R = q*V
    assert R == Vec3([-1, 1, -1]), 'got %s instead' % str(R)
    # neg angle
    q = Rot3(axis=Vec3([-1, -1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    q = Rot3(axis=-Vec3([-1, -1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([-1, 1, -1]), 'got %s instead' % str(R)
    # neg axis
    q = Rot3(axis=-Vec3([-1, -1, 1]), angle=tTurn)
    R = q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)

    # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis=Vec3([1, -1, 1]), angle=tTurn)
    V = Vec3([1, 1, 1])
    R = q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg angle
    q = Rot3(axis=Vec3([1, -1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    q = Rot3(axis=-Vec3([1, -1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg axis
    q = Rot3(axis=-Vec3([1, -1, 1]), angle=tTurn)
    R = q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)

    # test quat mul from above (instead of Vec3):
    # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis=Vec3([1, -1, 1]), angle=tTurn)
    V = Quat([0, 1, 1, 1])
    R = q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg angle
    q = Rot3(axis=Vec3([1, -1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    q = Rot3(axis=-Vec3([1, -1, 1]), angle=-tTurn)
    R = q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg axis
    q = Rot3(axis=-Vec3([1, -1, 1]), angle=tTurn)
    R = q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)

    # Axis Angle:
    V = Vec3([1, -1, 1])
    a = tTurn
    t = Rot3(axis=V, angle=a)
    rx = t.axis()
    x = V.normalise()
    RA = t.angle()
    assert (eq(RA, a) and rx == x) or (eq(RA, -a) and rx == -x), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, rx, a, x, -a, -x)
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # neg angle
    V = Vec3([1, -1, 1])
    a = -tTurn
    t = Rot3(axis=V, angle=a)
    rx = t.axis()
    x = V.normalise()
    RA = t.angle()
    assert (eq(RA, a) and rx == x) or (eq(RA, -a) and rx == -x), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, rx, a, x, -a, -x)
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # neg angle, neg axis
    V = Vec3([-1, 1, -1])
    a = -tTurn
    t = Rot3(axis=V, angle=a)
    rx = t.axis()
    x = V.normalise()
    RA = t.angle()
    assert (eq(RA, a) and rx == x) or (eq(RA, -a) and rx == -x), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, rx, a, x, -a, -x)
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # neg axis
    V = Vec3([-1, 1, -1])
    a = tTurn
    t = Rot3(axis=V, angle=a)
    rx = t.axis()
    x = V.normalise()
    RA = t.angle()
    assert (eq(RA, a) and rx == x) or (eq(RA, -a) and rx == -x), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, rx, a, x, -a, -x)
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # Q I
    V = Vec3([-1, 1, -1])
    a = math.pi/3
    t = Rot3(axis=V, angle=a)
    rx = t.axis()
    x = V.normalise()
    RA = t.angle()
    assert (eq(RA, a) and rx == x) or (eq(RA, -a) and rx == -x), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, rx, a, x, -a, -x)
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # Q II
    V = Vec3([-1, 1, -1])
    a = math.pi - math.pi/3
    t = Rot3(axis=V, angle=a)
    rx = t.axis()
    x = V.normalise()
    RA = t.angle()
    assert (eq(RA, a) and rx == x) or (eq(RA, -a) and rx == -x), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, rx, a, x, -a, -x)
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # Q III
    V = Vec3([-1, 1, -1])
    a = math.pi + math.pi/3
    t = Rot3(axis=V, angle=a)
    rx = t.axis()
    x = V.normalise()
    RA = t.angle()
    a = a - 2 * math.pi
    assert (eq(RA, a) and rx == x) or (eq(RA, -a) and rx == -x), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, rx, a, x, -a, -x)
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # Q IV
    V = Vec3([-1, 1, -1])
    a = - math.pi/3
    t = Rot3(axis=V, angle=a)
    rx = t.axis()
    x = V.normalise()
    RA = t.angle()
    assert (eq(RA, a) and rx == x) or (eq(RA, -a) and rx == -x), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, rx, a, x, -a, -x)
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot

    try:
        q = Quat([2, 1, 1, 1])
        Rot3(q)
        assert False
    except AssertionError:
        pass

    try:
        q = Quat([-1.1, 1, 1, 1])
        Rot3(q)
        assert False
    except AssertionError:
        pass

    try:
        q = Quat([0, 0, 0, 0])
        Rot3(q)
        assert False
    except AssertionError:
        pass

    # test equality for negative axis and negative angle
    R0 = Rot3(axis=Vec3([1, 2, 3]), angle=2)
    R1 = Rot3(-R0[0])
    assert R0 == R1

    # test order
    R0 = Rot3(axis=uz, angle=qTurn)
    R1 = Rot3(axis=ux, angle=qTurn)
    R = (R1 * R0) * ux # expected: R1(R0(x))
    assert R == uz, 'Expected: %s, got %s' % (uz, R)
    R = (R1 * R0)
    x = Rot3(axis=Vec3([1, -1, 1]), angle=tTurn)
    assert R == x, 'Expected: %s, got %s' % (x, R)
    R = (R0 * R1)
    x = Rot3(axis=Vec3([1, 1, 1]), angle=tTurn)
    assert R == x, 'Expected: %s, got %s' % (x, R)

    # test conversion to Mat
    # x-axis
    R = Rot3(axis=uz, angle=qTurn).matrix()
    # 0  -1  0
    # 1   0  0
    # 0   0  1
    x = Vec3([0, -1, 0])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([1, 0, 0])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([0, 0, 1])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])
    R = Rot3(axis=uz, angle=hTurn).matrix()
    # -1   0  0
    #  0  -1  0
    #  0   0  1
    x = Vec3([-1, 0, 0])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([0, -1, 0])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([0, 0, 1])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])
    R = Rot3(axis=uz, angle=-qTurn).matrix()
    #  0   1  0
    # -1   0  0
    #  0   0  1
    x = Vec3([0, 1, 0])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([-1, 0, 0])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([0, 0, 1])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])

    # y-axis
    R = Rot3(axis=uy, angle=qTurn).matrix()
    #  0   0   1
    #  0   1   0
    # -1   0   0
    x = Vec3([0, 0, 1])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([0, 1, 0])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([-1, 0, 0])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])
    R = Rot3(axis=uy, angle=hTurn).matrix()
    # -1   0   0
    #  0   1   0
    #  0   0  -1
    x = Vec3([-1, 0, 0])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([0, 1, 0])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([0, 0, -1])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])
    R = Rot3(axis=uy, angle=-qTurn).matrix()
    #  0   0  -1
    #  0   1   0
    #  1   0   0
    x = Vec3([0, 0, -1])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([0, 1, 0])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([1, 0, 0])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])

    # x-axis
    R = Rot3(axis=ux, angle=qTurn).matrix()
    # 1  0  0
    # 0  0 -1
    # 0  1  0
    x = Vec3([1, 0, 0])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([0, 0, -1])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([0, 1, 0])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])
    R = Rot3(axis=ux, angle=hTurn).matrix()
    #  1  0  0
    #  0 -1  0
    #  0  0 -1
    x = Vec3([1, 0, 0])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([0, -1, 0])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([0, 0, -1])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])
    R = Rot3(axis=ux, angle=-qTurn).matrix()
    #  1  0  0
    #  0  0  1
    #  0 -1  0
    x = Vec3([1, 0, 0])
    assert R[0] == x, 'Expected: %s, got %s' % (x, R[0])
    x = Vec3([0, 0, 1])
    assert R[1] == x, 'Expected: %s, got %s' % (x, R[1])
    x = Vec3([0, -1, 0])
    assert R[2] == x, 'Expected: %s, got %s' % (x, R[2])

    seed(700114) # constant seed to be able to catch errors
    for K in range(100):
        R0 = Rot3(axis=[2*random()-1, 2*random()-1, 2*random()-1],
                angle=random() * 2 * math.pi)
        R1 = Rot3(axis=[2*random()-1, 2*random()-1, 2*random()-1],
                angle=random() * 2 * math.pi)
        R = R0 * R1
        assert R0.isRot()
        assert not R0.isRefl()
        assert not R0.isRotInv()
        assert R1.isRot()
        assert not R1.isRefl()
        assert not R1.isRotInv()
        assert R.isRot()
        assert not R.isRefl()
        assert not R.isRotInv()
        assert R0 * R0.inverse() == E
        assert R1 * R1.inverse() == E
        assert R * R.inverse() == E

    #####################
    # Transform: Refl3
    #####################
    try:
        q = Quat([0, 0, 0, 0])
        Refl3(q)
        assert False
    except AssertionError:
        pass

    try:
        V = Vec3([0, 0, 0])
        Refl3(planeN=V)
        assert False
    except AssertionError:
        pass

    try:
        V = Vec3([1, 0, 0, 0])
        Refl3(planeN=V)
        assert False
    except AssertionError:
        pass

    try:
        V = Vec([1, 0])
        Refl3(planeN=V)
        assert False
    except IndexError:
        pass

    seed(700114) # constant seed to be able to catch errors
    for K in range(100):
        s0 = Refl3(planeN=Vec3([2*random()-1, 2*random()-1, 2*random()-1]))
        s1 = Refl3(planeN=Vec3([2*random()-1, 2*random()-1, 2*random()-1]))
        R = s0 * s1
        assert not s0.isRot()
        assert s0.isRefl()
        assert not s0.isRotInv(), "for i = %d: %s" % (K, str(s0))
        assert not s1.isRot()
        assert s1.isRefl()
        assert not s1.isRotInv()
        assert R.isRot()
        assert not R.isRefl()
        assert not R.isRotInv()
        assert (s0 * s0) == E, 'for i == %d' % K
        assert (s1 * s1) == E, 'for i == %d' % K
        assert R * R.inverse() == E

    # border cases
    s0 = Refl3(planeN=ux)
    s1 = Refl3(planeN=uy)
    R = s0 * s1
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(uz)
    R = s1 * s0
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(uz)

    s0 = Refl3(planeN=ux)
    s1 = Refl3(planeN=uz)
    R = s0 * s1
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(uy)
    R = s1 * s0
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(uy)

    s0 = Refl3(planeN=uy)
    s1 = Refl3(planeN=uz)
    R = s0 * s1
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(ux)
    R = s1 * s0
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(ux)

    s0 = Refl3(planeN=ux)
    s1 = Refl3(planeN=uy)
    s2 = Refl3(planeN=uz)
    R = s0 * s1 * s2
    assert not R.isRot()
    assert not R.isRefl()
    assert R.isRotInv()
    assert R == I

    # test order: 2 refl planes with 45 degrees in between: 90 rotation
    s0 = Refl3(planeN=Vec3([0, 3, 0]))
    s1 = Refl3(planeN=Vec3([-1, 1, 0]))
    R = (s1 * s0)
    x = Rot3(axis=uz, angle=qTurn)
    assert R == x, 'Expected: %s, got %s' % (x, R)
    R = (s0 * s1)
    x = Rot3(axis=uz, angle=-qTurn)
    assert R == x, 'Expected: %s, got %s' % (x, R)

    # tests eq reflection for opposite normals
    seed(760117) # constant seed to be able to catch errors
    for K in range(100):
        N = Vec3([2*random()-1, 2*random()-1, 2*random()-1])
        s0 = Refl3(planeN=N)
        s1 = Refl3(planeN=-N)
        assert s0 == s1, '{} should == {} (i={})'.format(s0, s1, K)
        R = s0 * s1
        assert R == E, 'refl*refl: {} should == {} (i={})'.format(R, E, K)

    # reflection in same plane: border cases
    bCases = [ux, uy, uz]
    for N in bCases:
        s0 = Refl3(planeN=N)
        s1 = Refl3(planeN=-N)
        assert s0 == s1, '{} should == {} (i={})'.format(s0, s1, N)
        R = s0 * s1
        assert R == E, 'refl*refl: {} should == {} (i={})'.format(R, E, N)

    #####################
    # Transform: Rotary inversion
    #####################

    # type: R*I == I*R and gives a rotary inversion (random)

    seed(700114) # constant seed to be able to catch errors
    for K in range(100):
        R0 = RotInv3(axis=[2*random()-1, 2*random()-1, 2*random()-1],
                    angle=random() * 2 * math.pi)
        R1 = RotInv3(axis=[2*random()-1, 2*random()-1, 2*random()-1],
                    angle=random() * 2 * math.pi)
        R = R0 * R1
        assert not R0.isRot()
        assert not R0.isRefl()
        assert R0.isRotInv()
        assert not R1.isRot()
        assert not R1.isRefl()
        assert R1.isRotInv()
        assert R.isRot()
        assert not R.isRefl()
        assert not R.isRotInv()
        assert R0 * R0.inverse() == E
        assert R1 * R1.inverse() == E
        assert R * R.inverse() == E

    #####################
    # Rot4:
    #####################
    R0 = Rot4(axialPlane=(Vec4([1, 0, 0, 0]), Vec4([0, 0, 0, 1])),
            angle=math.pi/3)
    V = Vec4([10, 2, 0, 6])
    R = R0 * V
    x = Quat([V[0], 1, -math.sqrt(3), V[3]])
    eqFloatMargin = 1.0e-14
    assert R == x, 'Expected: %s, got %s' % (x, R)

    seed(700114) # constant seed to be able to catch errors
    for K in range(100):
        x0 = Vec4([2*random()-1, 2*random()-1, 2*random()-1, 2*random()-1])
        # make sure orthogonal: x0*x1 + y0*y1 + z0*z1 + w0*w1 == 0
        W, x, y = (2*random()-1, 2*random()-1, 2*random()-1)
        z = (-W*x0[0] - x*x0[1] - y*x0[2])/ x0[3]
        x1 = Vec4([W, x, y, z])
        R0 = Rot4(axialPlane=(x0, x1), angle=random() * 2 * math.pi)
        x0 = Vec4([2*random()-1, 2*random()-1, 2*random()-1, 2*random()-1])
        W, x, y = (2*random()-1, 2*random()-1, 2*random()-1)
        # make sure orthogonal: x0*x1 + y0*y1 + z0*z1 + w0*w1 == 0
        z = (-W*x0[0] - x*x0[1] - y*x0[2])/ x0[3]
        x1 = Vec4([W, x, y, z])
        R1 = Rot4(axialPlane=(x0, x1), angle=random() * 2 * math.pi)
        R = R0 * R1
        assert R0.isRot()
        #assert not R0.isRefl()
        #assert not R0.isRotInv()
        assert R1.isRot()
        #assert not R1.isRefl()
        #assert not R1.isRotInv()
        assert R.isRot()
        #assert not R.isRefl()
        #assert not R.isRotInv()
        #assert R0 * R0.inverse() == E
        #assert R1 * R1.inverse() == E
        #assert R * R.inverse() == E
        for N in range(1, 12):
            #print 'n', N
            if N > 98:
                eqFloatMargin = 1.0e-12
            R0 = Rot4(axialPlane=(x0, x1), angle=2 * math.pi / N)
            R = R0
            for J in range(1, N):
                a = R.angle()
                #print 'n:', N, 'j:', J, 'a:', a
                assert eq(J * 2 * math.pi / N, a), 'j: {}, R: {}'.format(
                    J, 2 * math.pi / N / a)
                R = R0 * R
            RA = R.angle()
            assert eq(RA, 0) or eq(RA, 2*math.pi), R.angle()

    #####################
    # DoubleRot4:
    #####################
    R0 = DoubleRot4(axialPlane=(Vec4([1, 0, 0, 0]), Vec4([0, 0, 0, 1])),
                    # 1/6 th and 1/8 th turn
                    angle=(math.pi/3, math.pi/4))
    V = Vec4([6, 2, 0, 6])
    R = R0 * V
    x = Quat([0, 1, -math.sqrt(3), math.sqrt(72)])
    eqFloatMargin = 1.0e-14
    assert R0.isRot()
    assert R == x, 'Expected: %s, got %s' % (x, R)
    R = E
    for K in range(23):
        R = R0 * R
        OOPS_MSG = 'oops for i = {}'.format(K)
        assert R.isRot(), OOPS_MSG
        RA = R.angle()
        #print 'angle:', 180*RA / math.pi
        #print  R * V
        assert not eq(RA, 0) and not eq(RA, 2*math.pi), RA
    R = R0 * R
    assert R.isRot()
    RA = R.angle()
    #print 'angle:', 180*RA / math.pi
    #print  R * V
    assert eq(RA, 0) or eq(RA, 2*math.pi), R.angle()

    R0 = DoubleRot4(axialPlane=(Vec4([1, 0, 0, 0]), Vec4([0, 0, 0, 1])),
                    # 1/6 th and 1/8 th turn:
                    angle=(math.pi/4, math.pi/3))
    V = Vec4([6, 2, 2, 0])
    R = R0 * V
    x = Quat([3, math.sqrt(8), 0, 3*math.sqrt(3)])
    eqFloatMargin = 1.0e-14
    assert R0.isRot()
    assert R == x, 'Expected: %s, got %s' % (x, R)
    R = E
    for K in range(23):
        R = R0 * R
        OOPS_MSG = 'oops for i = {}'.format(K)
        assert R.isRot(), OOPS_MSG
        RA = R.angle()
        #print 'angle:', 180*RA / math.pi
        #print  R * V
        assert not eq(RA, 0) and not eq(RA, 2*math.pi), RA
    R = R0 * R
    assert R.isRot()
    RA = R.angle()
    #print 'angle:', 180*RA / math.pi
    #print  R * V
    assert eq(RA, 0) or eq(RA, 2*math.pi), R.angle()

    # test if vectors in axial plane are not changed.
    V0 = Vec4([1, 1, 1, 0])
    V1 = Vec4([0, 0, 1, 1])
    V1 = V1.makeOrthogonalTo(V0)
    R0 = DoubleRot4(axialPlane=(V1, V0),
                    # 1/6 th and 1/8 th turn:
                    angle=(math.pi/4, math.pi/3))
    for K in range(5):
        V = V0 + K * V1
        R = R0 * V
        x = V
        assert eq(RA, 0) or eq(RA, 2*math.pi), "{}: expected: {}, got: {}".format(
            K, x, R)
        V = K * V0 + V1
        R = R0 * V
        x = V
        assert eq(RA, 0) or eq(RA, 2*math.pi), "{}: expected: {}, got: {}".format(
            K, x, R)

    #####################
    # Mat
    #####################
    M = Mat([Vec([1, 2, 3]),
            Vec([0, 2, 1]),
            Vec([1, -1, 3])])

    L = M.rows
    W = M.cols

    assert M.det() == M.T().det()
    assert M == M.T().T()

    T = M.T()

    for K in range(L):
        R = M.deleteRow(K)
        assert R.rows == L-1
        assert R.cols == W
        assert R == M.deleteRow(-(L-K))
        N = T.T()
        N.pop(K)
        assert R == N

    for K in range(W):
        R = M.deleteCol(K)
        assert R.rows == L
        assert R.cols == W-1
        assert R == M.deleteCol(-(W-K))
        T = M.T()
        T.pop(K)
        assert R == T.T()

    # don't want to test an orthogonal matrix,
    # since then the inverse method calls: det, deleteRow, -Col, and transpose.
    assert not M.orthogonal()
    M_I = M.inverse()
    assert M * M_I == Mat()
    assert M_I * M == Mat()
    B = Vec([1, 2, 3])
    assert M.solve(B) == M_I * B

    print 'All tests passed'
