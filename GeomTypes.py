#! /usr/bin/python
"""
Module with geometrical types.
"""
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

from __future__ import print_function
import math
import indent


def turn(r):
    """Return angle in radians of r times a whole turn"""
    return r * 2 * math.pi


def to_radians(r):
    """Convert angle in degrees to radians"""
    return math.pi * r / 180


def to_degrees(r):
    """Convert angle in radians to degrees"""
    return 180.0 * r / math.pi


FULL_TURN = turn(1)
HALF_TURN = turn(0.5)
QUARTER_TURN = turn(0.25)
THIRD_TURN = turn(1.0/3)

DEFAULT_EQ_FLOAT_MARGIN = 1.0e-10
DEFAULT_ROUND_FLOAT_MARGIN = 10

# Disable pylint warning: Constant name "_eq_float_margin" doesn't conform to
# UPPER_CASE naming style (invalid-name)
# Below isn't a constant, it is a variable that can be changed by a function
_eq_float_margin = DEFAULT_EQ_FLOAT_MARGIN  # pylint: disable=C0103


def set_eq_float_margin(margin):
    """Set the margin to be used for floats to be considered equal

    The value can be set back to its default by reset_eq_float_margin"""
    # Note sure how to do this in a better and simple way (without introducing
    # a class) without pylint warning about it.
    global _eq_float_margin  # pylint: disable=W0603,C0103
    _eq_float_margin = margin


def reset_eq_float_margin():
    """Reset the margin to be used for floats to be considered equal

    This function can be used after calling set_eq_float_margin
    It is set back to the default: DEFAULT_EQ_FLOAT_MARGIN
    """
    set_eq_float_margin(DEFAULT_EQ_FLOAT_MARGIN)


def eq(a, b, margin=None):
    """
    Check if 2 floats 'a' and 'b' are close enough to be called equal.

    a: a floating point number.
    b: a floating point number.
    margin: if |a - b| < margin then the floats will be considered equal and
            True is returned. Optional parameter. If not set, then a standard
            value is used. That standard value can be set with
            set_eq_float_margin.
    """
    if margin is None:
        margin = _eq_float_margin
    return abs(a - b) < margin


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


def _get_mat_rot(w, x, y, z, sign=1):
    """Return matrix for a quarternion that is supposed to represent a rotation

    The function won't check that the quarternion really represents a rotation.
    """
    dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
    dxw, dyw, dzw = 2*x*w, 2*y*w, 2*z*w
    dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
    return [
        Vec([sign*(1-dy2-dz2), sign*(dxy-dzw), sign*(dxz+dyw)]),
        Vec([sign*(dxy+dzw), sign*(1-dx2-dz2), sign*(dyz-dxw)]),
        Vec([sign*(dxz-dyw), sign*(dyz+dxw), sign*(1-dx2-dy2)])]


class NoRotation(Exception):
    """The transform doesn't represent a rotation"""
    pass


class UnsupportedTransform(Exception):
    """This isn't a transform or it isn't supported."""
    pass


class UnsupportedOperand(Exception):
    """One of the operand aren't supported for this operation"""
    pass


# Use tuples instead of lists to enable building sets used for isometries
class Vec(tuple):
    """Define a Euclidean vector"""
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
            for i in range(1, len(self)):
                s = '%s, %s' % (s, self[i])
            return '%s]' % s
        except IndexError:
            return '[]'

    def __add__(self, w):
        return self.__class__([a + b for a, b in zip(self, w)])

    def __radd__(self, w):
        # provide __radd__ for [..] + Vec([..])
        # print 'v', self, 'w', w
        return self.__class__([a + b for a, b in zip(self, w)])

    def __sub__(self, w):
        return self.__class__([a - b for a, b in zip(self, w)])

    def __rsub__(self, w):
        # provide __rsub__ for [..] + Vec([..])
        return self.__class__([b - a for a, b in zip(self, w)])

    def __eq__(self, w):
        try:
            r = len(self) == len(w)
        except TypeError:
            return False
        for a, b in zip(self, w):
            if not r:
                break
            r = r and eq(a, b)
        return r

    def __ne__(self, w):
        return not self == w

    def __neg__(self):
        return self.__class__([-a for a in self])

    def __mul__(self, w):
        if isinstance(w, tuple):
            # dot product
            r = 0
            for a, b in zip(self, w):
                r += a*b
            return r
        if isinstance(w, (int, float)):
            return self.__class__([w*a for a in self])
        raise UnsupportedOperand(
            "Right-hand operand of type {} isn't supported with Vec".format(
                type(w)))

    def __rmul__(self, w):
        if isinstance(w, tuple):
            # provide __rmul__ for [..] + Vec([..])
            # dot product
            r = 0
            for a, b in zip(self, w):
                r += a*b
            return r
        if isinstance(w, (int, float)):
            return self.__class__([w*a for a in self])
        raise UnsupportedOperand(
            "Right-hand operand of type {} isn't supported with Vec".format(
                type(w)))

    def __div__(self, w):
        if isinstance(w, (int, float)):
            return self.__class__([a/w for a in self])
        raise UnsupportedOperand(
            "Right-hand operand of type {} isn't supported with Vec".format(
                type(w)))

    def squared_norm(self):
        """Return the squared norm of this vector"""
        r = 0
        for a in self:
            r += a*a
        return r

    def norm(self):
        """Return the norm of this vector"""
        return math.sqrt(self.squared_norm())

    def normalise(self):
        """Return a new vector that is the normalised version of this one"""
        return self / self.norm()

    normalize = normalise

    def angle(self, w):
        """Return the angle between two (2D) vectors"""
        return math.acos(self.normalise()*w.normalise())

    # TODO cross product from GA?


class Vec3(Vec):
    """Define a Euclidean vector in 3D"""
    def __new__(cls, v):
        return Vec.__new__(cls, [float(v[i]) for i in range(3)])

    def cross(self, w):
        "Return the cross product of this vector with 'w'"""
        return self.__class__([
            self[1] * w[2] - self[2] * w[1],
            self[2] * w[0] - self[0] * w[2],
            self[0] * w[1] - self[1] * w[0]])

    # TODO implement Scenes3D.getAxis2AxisRotation here


UX = Vec3([1, 0, 0])
UY = Vec3([0, 1, 0])
UZ = Vec3([0, 0, 1])


class Vec4(Vec):
    """Define a Euclidean vector in 4D"""
    def __new__(cls, v):
        return Vec.__new__(cls, [float(v[i]) for i in range(4)])

    def is_parallel(self, v):
        """Return whether 'v' is parallel to this vector"""
        z0 = z1 = z2 = z3 = False  # expresses whether self[i] == v[i] == 0
        q0, q1, q2, q3 = 1, 2, 3, 4  # initialise all differently
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
        if not z1:
            return (z0 or eq(q1, q0)) and \
                (z2 or eq(q1, q2)) and \
                (z3 or eq(q1, q3))
        if not z2:
            return (z0 or eq(q2, q0)) and \
                (z1 or eq(q2, q1)) and \
                (z3 or eq(q2, q3))
        if not z3:
            return (z0 or eq(q3, q0)) and \
                (z1 or eq(q3, q1)) and \
                (z2 or eq(q3, q2))
        # else z0 and z1 and z2 and z3, i.e self == v == (0, 0, 0, 0)
        return True

    def make_orthogonal_to(self, v):
        """
        Returns the modification of this vector orthogonal to v.

        While keeping them in the same plane.
        """
        w = self
        # say v = [vx, vy, vz, vw]
        # and w = [wx, wy, wz, ww]
        # Now we change w into w' by a linear combination of v and w, so that
        # w' still lies in the plane spanned by v and w:
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
        assert not w.is_parallel(v), \
            'null vector used or vectors are (too) parallel; self = ' + \
            w.__repr__() + '; v = ' + v.__repr__()
        # TODO: is there a better way to set,...
        return Vec4(p * v + q * w)

    def cross(self, v, w):
        """Return cross product of 3 vectors"""
        vw_xy = v[0] * w[1] - v[1] * w[0]
        vw_xz = v[0] * w[2] - v[2] * w[0]
        vw_xw = v[0] * w[3] - v[3] * w[0]
        vw_yz = v[1] * w[2] - v[2] * w[1]
        vw_yw = v[1] * w[3] - v[3] * w[1]
        vw_zw = v[2] * w[3] - v[3] * w[2]
        return Vec4([
            +self[1] * vw_zw - self[2] * vw_yw + self[3] * vw_yz,
            -self[0] * vw_zw + self[2] * vw_xw - self[3] * vw_xz,
            +self[0] * vw_yw - self[1] * vw_xw + self[3] * vw_xy,
            -self[0] * vw_yz + self[1] * vw_xz - self[2] * vw_xy
        ])


def unit_vec4(i):
    """Return a unit vector in 4D along 'i' axis"""
    v = [0, 0, 0, 0]
    v[i] = 1
    return Vec4(v)


class Quat(Vec):
    """Define a quarternion"""
    def __new__(cls, v=None):
        # if 3D vector, use it to set vector part only and use 0 for scalar
        if len(v) == 3:
            v = [0, v[0], v[1], v[2]]
        return super(Quat, cls).__new__(cls, [float(v[i]) for i in range(4)])

    def __init__(self, *args, **kwargs):
        super(Quat, self).__init__(*args, **kwargs)
        self.__cache__ = {}

    def conjugate(self):
        """Return conjugate for this quarternion"""
        return self.__class__([self[0], -self[1], -self[2], -self[3]])

    def __mul__(self, w):
        if isinstance(w, Quat):
            v = self
            # Quaternion product
            return self.__class__([
                v[0]*w[0] - v[1]*w[1] - v[2] * w[2] - v[3] * w[3],
                v[0]*w[1] + v[1]*w[0] + v[2] * w[3] - v[3] * w[2],
                v[0]*w[2] - v[1]*w[3] + v[2] * w[0] + v[3] * w[1],
                v[0]*w[3] + v[1]*w[2] - v[2] * w[1] + v[3] * w[0]])
        if isinstance(w, (float, int)):
            return Vec.__mul__(self, w)
        raise UnsupportedOperand(
            "Right-hand operand of type {} isn't supported with Quat".format(
                type(w)))

    def dot(self, w):
        """Return the dot product between this quarternion and w"""
        return Vec.__mul__(self, w)

    def scalar(self):
        """Return the scalar part of self"""
        return self[0]

    def vector(self):
        """Return the vector part of self (as a Vec3)"""
        if 'vector_part' not in self.__cache__:
            self.__cache__['vector_part'] = Vec3(self[1:])
        return self.__cache__['vector_part']

    inner = dot
    S = scalar
    V = vector


def _transform3_type_str(i):
    """Return string representation of the kind of transform for Transform3

    If this isn't a proper transform, then 'Transform3' is returned
    """
    if i == Transform3.Rot:
        return 'Rot3'
    if i == Transform3.Refl:
        return 'Refl3'
    if i == Transform3.RotInv:
        return 'RotInv3'
    return 'Transform3'


def _is_quat_pair(q):
    """Check qhether q is a pair of Quat (quaternions)

    This is used for input parameter checking
    """
    return (
        q is not None and
        len(q) == 2 and isinstance(q[0], Quat) and isinstance(q[1], Quat)
    )


class Transform3(tuple):
    """Define a 3D tranformation using quarternions"""
    debug = False
    eq_float_margin = _eq_float_margin

    def __new__(cls, quatPair):
        assert_str = "A 3D transform is represented by 2 quaternions: "
        assert len(quatPair) == 2, assert_str + str(quatPair)
        assert isinstance(quatPair[0], Quat), assert_str + str(quatPair)
        assert isinstance(quatPair[1], Quat), assert_str + str(quatPair)
        return super(Transform3, cls).__new__(cls, quatPair)

    def __init__(self, *args, **kwargs):
        super(Transform3, self).__init__(*args, **kwargs)
        self.__cache__ = {}

    def __repr__(self):
        s = indent.Str('%s((\n' % (_transform3_type_str(self.type())))
        s = s.add_incr_line('%s,' % repr(Quat(self[0])))
        s = s.add_line('%s,' % repr(Quat(self[1])))
        s = s.add_decr_line('))')
        if __name__ != '__main__':
            s = s.insert('%s.' % __name__)
        return s

    def __hash__(self):
        if 'hash_nr' not in self.__cache__:
            if self.isRot():
                self.__cache__['hash_nr'] = self.__hashRot__()
            elif self.isRefl():
                self.__cache__['hash_nr'] = self.__hashRefl__()
            elif self.isRotInv():
                self.__cache__['hash_nr'] = self.__hashRotInv__()
            else:
                raise UnsupportedTransform("Not a (supported) transform")
        return self.__cache__['hash_nr']

    def __str__(self):
        if self.isRot():
            return self.__strRot()
        if self.isRefl():
            return self.__strRefl()
        if self.isRotInv():
            return self.__strRotInv()
        # non-proper transform: show the quaternion pair.
        return '%s * .. * %s' % (str(self[0]), str(self[1]))

    def to_orbit_str(self, prec=DEFAULT_ROUND_FLOAT_MARGIN):
        """Return the orbit file format representation for this transform.

        If this is not a proper transform, then UnsupportedTransform is raised
        """
        if self.isRot():
            return self.__rot2orbit(prec)
        if self.isRefl():
            return self.__refl2orbit(prec)
        if self.isRotInv():
            return self.__rotinv2orbit(prec)
        raise UnsupportedTransform("Not a (supported) transform")

    def __mul__(self, u):
        if isinstance(u, Transform3):
            # self * u =  wLeft * vLeft .. vRight * wRight
            return Transform3([self[0] * u[0], u[1] * self[1]])
        # TODO: check kind of Transform3 and optimise
        if isinstance(u, Vec) and len(u) == 3:
            return (self[0] * Quat([0, u[0], u[1], u[2]]) * self[1]).V()
        if isinstance(u, Quat):
            return (self[0] * u * self[1]).V()
        return u.__rmul__(self)

    def __eq__(self, u):
        if not isinstance(u, Transform3):
            return False
        if self.isRot() and u.isRot():
            is_eq = self.__eqRot(u)
        elif self.isRefl() and u.isRefl():
            is_eq = self.__eqRefl(u)
        elif self.isRotInv() and u.isRotInv():
            is_eq = self.__eqRotInv(u)
        else:
            is_eq = self[0] == u[0] and self[1] == u[1]
            if is_eq:
                print('fallback:',
                      self[0], '==', u[0], 'and', self[1], '==', u[1])
            assert not is_eq, \
                'oops, fallback: unknown transform \n{}\nor\n{}'.format(
                    str(self), str(u))
            return is_eq
        if (is_eq and (self.__hash__() != u.__hash__())):
            print('\n*** warning hashing will not work between\n' +
                  '{} and\n{}'.format(str(self), str(u)))
        return is_eq

    def __ne__(self, u):
        return not self == u

    Rot = 0
    Refl = 1
    RotInv = 2
    RotRefl = RotInv

    def type(self):
        """Return what kind of transform this is.

        This can be any of:
            self.Rot: for a rotation
            self.Refl: for a reflection
            self.RotInv: for a rotary inversion (which is the same as a rotary
                         reflection.
        """
        if self.isRot():
            return self.Rot
        if self.isRefl():
            return self.Refl
        if self.isRotInv():
            return self.RotInv
        raise UnsupportedTransform(
            "Not a (supported) transform: {} != 1?".format(self[1].norm()))

    def angle(self):
        """In case this transform contains a rotation, return the angle

        Otherwise raise a NoRotation exception
        The angle is returned in radians.
        """
        if self.isRot():
            return self._angleRot()
        if self.isRotInv():
            return self._angleRotInv()
        raise NoRotation(
            'oops, unknown angle; transform {}\n'.format(str(self)) +
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )

    def axis(self):
        """In case this transform contains a rotation, return the axis

        Otherwise raise a NoRotation exception
        """
        if self.isRot():
            return self._axisRot()
        if self.isRotInv():
            return self._axisRotInv()
        raise NoRotation(
            'oops, unknown axis; transform {}\n'.format(str(self)) +
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )

    def glMatrix(self):
        """Return the glMatrix representation of this transform"""
        if self.isRot():
            m = self._glMatrixRot()
        elif self.isRefl():
            m = self._matrixRefl()
        elif self.isRotInv():
            m = self._glMatrixRotInv()
        else:
            raise UnsupportedTransform(
                'oops, unknown matrix; transform {}\n'.format(str(self)))
        return Mat([Vec([m[0][0], m[0][1], m[0][2], 0]),
                    Vec([m[1][0], m[1][1], m[1][2], 0]),
                    Vec([m[2][0], m[2][1], m[2][2], 0]),
                    Vec([0, 0, 0, 1])])

    def matrix(self):
        """Return the matrix representation of this transform"""
        if self.isRot():
            return self._matrixRot()
        if self.isRefl():
            return self._matrixRefl()
        if self.isRotInv():
            return self._matrixRotInv()
        raise UnsupportedTransform(
            'oops, unknown matrix; transform {}\n'.format(str(self)))

#    def matrix4(self):
#        m = self.matrix()
#        return Mat([
#                Vec([m[0][0], m[0][1], m[0][2], 0]),
#                Vec([m[1][0], m[1][1], m[1][2], 0]),
#                Vec([m[2][0], m[2][1], m[2][2], 0]),
#                Vec([0,       0,       0,       1]),
#            ])

    def inverse(self):
        """Return a new object with the inverse of this transform"""
        if self.isRot():
            return self._inverseRot()
        if self.isRefl():
            return self._inverseRefl()
        if self.isRotInv():
            return self._inverseRotInv()
        raise UnsupportedTransform(
            'oops, unknown matrix; transform {}\n'.format(str(self)))

    def is_direct(self):
        """Return whether this is an opposite transform (i.e. not direct)"""
        return self.isRot()

    def is_opposite(self):
        """Return whether this is an opposite transform (i.e. not direct)"""
        return not self.is_direct()

    # *** ROTATION specific functions:
    def isRot(self):
        """Return whether this tranform is a rotation."""
        d = 1 - self.eq_float_margin
        _margin = 1 - d * d
        eqSquareNorm = eq(self[1].squared_norm(), 1, margin=_margin)
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
        axis = self._axisRot()
        return hash((self.Rot,
                     round(self._angleRot(), DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[0], DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[1], DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[2], DEFAULT_ROUND_FLOAT_MARGIN)))

    def __strRot(self):
        axis = self._axisRot()
        return 'Rotation of {} degrees around [{}, {}, {}]'.format(
            float2str(
                to_degrees(self._angleRot()), DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[0], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[1], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[2], DEFAULT_ROUND_FLOAT_MARGIN))

    def __rot2orbit(self, prec=DEFAULT_ROUND_FLOAT_MARGIN):
        axis = self._axisRot()
        return 'R {} {} {} {}'.format(
            float2str(self._angleRot(), prec),
            float2str(axis[0], prec),
            float2str(axis[1], prec),
            float2str(axis[2], prec))

    def _angleRot(self):
        if 'angleRot' not in self.__cache__:
            self._define_unique_angle_axis()
        return self.__cache__['angleRot']

    def _axisRot(self):
        if 'axisRot' not in self.__cache__:
            self._define_unique_angle_axis()
        return self.__cache__['axisRot']

    def _define_unique_angle_axis(self):
        # rotation axis
        try:
            self.__cache__['axisRot'] = self[0].V().normalise()
        except ZeroDivisionError:
            assert self[0] == Quat([1, 0, 0, 0]) or \
                self[0] == Quat([-1, 0, 0, 0]), \
                "{} doesn'self represent a rotation".format(self.__repr__())
            self.__cache__['axisRot'] = self[0].V()
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
        self.__cache__['angleRot'] = 2 * math.atan2(sin, cos)

        # make unique: -pi < angle < pi
        if not (self.__cache__['angleRot'] < math.pi
                or eq(self.__cache__['angleRot'], math.pi)):
            self.__cache__['angleRot'] = self.__cache__['angleRot'] - \
                2 * math.pi
        if not (self.__cache__['angleRot'] > -math.pi
                or eq(self.__cache__['angleRot'], -math.pi)):
            self.__cache__['angleRot'] = self.__cache__['angleRot'] + \
                2 * math.pi

        # make unique: 0 < angle < pi
        if eq(self.__cache__['angleRot'], 0):
            self.__cache__['angleRot'] = 0.0
        if self.__cache__['angleRot'] < 0:
            self.__cache__['angleRot'] = -self.__cache__['angleRot']
            self.__cache__['axisRot'] = -self.__cache__['axisRot']
        if eq(self.__cache__['angleRot'], math.pi):
            # if halfturn, make axis unique: make the first non-zero element
            # positive:
            if eq(self.__cache__['axisRot'][0], 0):
                self.__cache__['axisRot'] = Vec3(
                    [0.0,
                     self.__cache__['axisRot'][1],
                     self.__cache__['axisRot'][2]])
            if self.__cache__['axisRot'][0] < 0:
                self.__cache__['axisRot'] = -self.__cache__['axisRot']
            elif self.__cache__['axisRot'][0] == 0:
                if eq(self.__cache__['axisRot'][1], 0):
                    self.__cache__['axisRot'] = Vec3(
                        [0.0, 0.0, self.__cache__['axisRot'][2]])
                if self.__cache__['axisRot'][1] < 0:
                    self.__cache__['axisRot'] = -self.__cache__['axisRot']
                elif self.__cache__['axisRot'][1] == 0:
                    # not valid axis: if eq(self.__cache__['axisRot'][2], 0):
                    if self.__cache__['axisRot'][2] < 0:
                        self.__cache__['axisRot'] = -self.__cache__['axisRot']
        elif eq(self.__cache__['angleRot'], 0):
            self.__cache__['angleRot'] = 0.0
            self.__cache__['axisRot'] = Vec3([1.0, 0.0, 0.0])

    def _matrixRot(self):
        if 'matrix_rot' not in self.__cache__:
            w, x, y, z = self[0]
            self.__cache__['matrix_rot'] = _get_mat_rot(w, x, y, z)
        return self.__cache__['matrix_rot']

    def _glMatrixRot(self):
        if 'gl_matrix_rot' not in self.__cache__:
            w, x, y, z = self[0]
            self.__cache__['gl_matrix_rot'] = _get_mat_rot(-w, x, y, z)
        return self.__cache__['gl_matrix_rot']

    def _inverseRot(self):
        if 'inverse_rot' not in self.__cache__:
            self.__cache__['inverse_rot'] = Rot3(axis=self.axis(),
                                                 angle=-self.angle())
        return self.__cache__['inverse_rot']

    # *** REFLECTION specific functions:
    def isRefl(self):
        """Return whether this tranform is a reflection."""
        return (
            self[1] == self[0]
            and
            eq(self[1].squared_norm(), 1)
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
                self.Refl,  # to use a tuple of 5 elements for all types
                round(normal[0], DEFAULT_ROUND_FLOAT_MARGIN),
                round(normal[1], DEFAULT_ROUND_FLOAT_MARGIN),
                round(normal[2], DEFAULT_ROUND_FLOAT_MARGIN)
            )
        )

    def __strRefl(self):
        norm = self.planeN()
        return 'Reflection in plane with normal [{}, {}, {}]'.format(
            float2str(norm[0], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(norm[1], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(norm[2], DEFAULT_ROUND_FLOAT_MARGIN))

    def __refl2orbit(self, prec=DEFAULT_ROUND_FLOAT_MARGIN):
        norm = self.planeN()
        return 'S {} {} {}'.format(
            float2str(norm[0], prec),
            float2str(norm[1], prec),
            float2str(norm[2], prec))

    def planeN(self):
        """If this is a reflection, return the plane normal.

        Should only be called when this is a reflection.
        """
        if 'plane_normal' not in self.__cache__:
            self.__cache__['plane_normal'] = self[0].V()
            # make normal unique: make the first non-zero element positive:
            if eq(self.__cache__['plane_normal'][0], 0):
                self.__cache__['plane_normal'] = Vec3(
                    [0.0,
                     self.__cache__['plane_normal'][1],
                     self.__cache__['plane_normal'][2]])
            if self.__cache__['plane_normal'][0] < 0:
                self.__cache__['plane_normal'] = -self.__cache__[
                    'plane_normal']
            elif self.__cache__['plane_normal'][0] == 0:
                if eq(self.__cache__['plane_normal'][1], 0):
                    self.__cache__['plane_normal'] = Vec3(
                        [0.0, 0.0, self.__cache__['plane_normal'][2]])
                if self.__cache__['plane_normal'][1] < 0:
                    self.__cache__['plane_normal'] = -self.__cache__[
                        'plane_normal']
                elif self.__cache__['plane_normal'][1] == 0:
                    # not needed (since not valid axis):
                    # if eq(self.__cache__['plane_normal'][2], 0):
                    if self.__cache__['plane_normal'][2] < 0:
                        self.__cache__['plane_normal'] = -self.__cache__[
                            'plane_normal']
        return self.__cache__['plane_normal']

    def _matrixRefl(self):
        if 'matrix_refl' not in self.__cache__:
            _, x, y, z = self[0]
            dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
            dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
            self.__cache__['matrix_refl'] = [
                Vec([1-dx2, -dxy, -dxz]),
                Vec([-dxy, 1-dy2, -dyz]),
                Vec([-dxz, -dyz, 1-dz2]),
            ]
        return self.__cache__['matrix_refl']

    def _inverseRefl(self):
        return self

    # *** ROTARY INVERSION (= ROTARY RELECTION) specific functions:
    def I(self):
        """Apply a central inversion on this transform."""
        if 'central_inverted' not in self.__cache__:
            self.__cache__['central_inverted'] = Transform3(
                [-self[0], self[1]])
        return self.__cache__['central_inverted']

    def isRotInv(self):
        """Return whether the transform is a rotary inversion."""
        return self.I().isRot() and not self.isRefl()

    def __eqRotInv(self, u):
        return self.I() == u.I()

    def __hashRotInv__(self):
        axis = self._axisRotInv()
        return hash((self.Rot,
                     round(self._angleRotInv(), DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[0], DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[1], DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[2], DEFAULT_ROUND_FLOAT_MARGIN)))

    def __strRotInv(self):
        r = self.I()
        axis = r.axis()
        return 'Rotary inversion of {} degrees around [{}, {}, {}]'.format(
            float2str(to_degrees(r.angle()), DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[0], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[1], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[2], DEFAULT_ROUND_FLOAT_MARGIN))

    def __rotinv2orbit(self, prec=DEFAULT_ROUND_FLOAT_MARGIN):
        """If this is a rotary inversion, return orbit file format string repr.

        Should only be called when this is a rotary inversion
        """
        r = self.I()
        return 'I' + r.to_orbit_str(prec)[1:]

    def _angleRotInv(self):
        """If this is a rotary inversion, return the angle.

        Make sure to only call this method when this is a rotary inversion
        """
        return self.I().angle()

    def _axisRotInv(self):
        """If this is a rotary inversion, return the axis.

        Make sure to only call this method when this is a rotary inversion
        """
        return self.I().axis()

    def _matrixRotInv(self):
        """If this is a rotary inversion, return the matrix representation.

        Should only be called when this is a rotary inversion
        """
        if 'matrix_rot_inv' not in self.__cache__:
            w, x, y, z = self[0]
            self.__cache__['matrix_rot_inv'] = _get_mat_rot(w, x, y, z, -1)
        return self.__cache__['matrix_rot_inv']

    def _glMatrixRotInv(self):
        """If this is a rotary inversion, return the glMatrix.

        Should only be called when this is a rotary inversion
        """
        if 'gl_matrix_rot_inv' not in self.__cache__:
            w, x, y, z = self[0]
            self.__cache__['gl_matrix_rot_inv'] = _get_mat_rot(-w, x, y, z, -1)
        return self.__cache__['gl_matrix_rot_inv']

    def _inverseRotInv(self):
        """If this is a rotary inversion, return the reverse.

        Should only be called when this is a rotary inversion
        """
        if 'inverse_rot_inv' not in self.__cache__:
            self.__cache__['inverse_rot_inv'] = RotInv3(axis=self.axis(),
                                                        angle=-self.angle())
        return self.__cache__['inverse_rot_inv']

    isRotRefl = isRotInv
    _axisRotRefl = _axisRotInv

    def angleRotRefl(self):
        """Return the angle of a rotary reflection."""
        return self._angleRotInv() - HALF_TURN


class Rot3(Transform3):
    """Define a rotation in 3D"""
    def __new__(cls, quat=None, axis=Vec3([1, 0, 0]), angle=0):
        """
        Initialise a 3D rotation
        axis: axis to rotate around: doesn't need to be normalised
        angle: angle in radians to rotate
        """
        if _is_quat_pair(quat):
            trans = Transform3.__new__(cls, quat)
            assert trans.isRot(), "%s doesn't represent a rotation" % str(quat)
            return trans
        elif isinstance(quat, Quat):
            try:
                quat = quat.normalise()
            except ZeroDivisionError:
                pass  # will fail on assert below:
            trans = Transform3.__new__(cls, [quat, quat.conjugate()])
            assert trans.isRot(), "%s doesn't represent a rotation" % str(quat)
            return trans
        else:
            # quat = cos(angle) + y sin(angle)
            alpha = angle / 2
            # if axis is specified as e.g. a list:
            if not isinstance(axis, Vec):
                axis = Vec3(axis)
            if axis != Vec3([0, 0, 0]):
                axis = axis.normalise()
            quat = math.sin(alpha) * axis
            quat = Quat([math.cos(alpha), quat[0], quat[1], quat[2]])
            return Transform3.__new__(cls, [quat, quat.conjugate()])


class HalfTurn3(Rot3):
    """Define a half-turn (rotation)

    qLeft: ignored argument added to be compatible with Rot3
    axis: named argument holding the axis to rotate around
    angle: ignored argument added to be compatible with Rot3
    """
    def __new__(cls, qLeft=None, axis=None, angle=0):
        del qLeft, angle
        assert axis is not None, "You must specify an axis"
        return Rot3.__new__(cls, axis=axis, angle=HALF_TURN)


class Rotx(Rot3):
    """Define a rotation around the x-axis

    qLeft: ignored argument added to be compatible with Rot3
    axis: ignored argument added to be compatible with Rot3
    angle: named argument holding the rotation angle in radians
    """
    def __new__(cls, qLeft=None, axis=None, angle=0):
        del qLeft, axis
        return Rot3.__new__(cls, axis=UX, angle=angle)


class Roty(Rot3):
    """Define a rotation around the y-axis

    qLeft: ignored argument added to be compatible with Rot3
    axis: ignored argument added to be compatible with Rot3
    angle: named argument holding the rotation angle in radians
    """
    def __new__(cls, qLeft=None, axis=None, angle=0):
        del qLeft, axis
        return Rot3.__new__(cls, axis=UY, angle=angle)


class Rotz(Rot3):
    """Define a rotation around the z-axis

    qLeft: ignored argument added to be compatible with Rot3
    axis: ignored argument added to be compatible with Rot3
    angle: named argument holding the rotation angle in radians
    """
    def __new__(cls, qLeft=None, axis=None, angle=0):
        del qLeft, axis
        return Rot3.__new__(cls, axis=UZ, angle=angle)


class Refl3(Transform3):
    """Define a rotation in 3D"""
    def __new__(cls, quat=None, planeN=None):
        """Define a 3D reflection is a plane

        Either define
        quat: quaternion representing the left (and right) quaternion
        multiplication for a reflection
        or
        planeN: the 3D normal of the plane in which the reflection takes place.
        """
        result = None
        if _is_quat_pair(quat):
            result = Transform3.__new__(cls, quat)
            assert result.isRefl(), "%s doesn't represent a reflection" % str(
                quat)
        elif isinstance(quat, Quat):
            try:
                quat = quat.normalise()
            except ZeroDivisionError:
                pass  # will fail on assert below:
            result = Transform3.__new__(cls, [quat, quat])
            assert result.isRefl(), "%s doesn't represent a reflection" % str(
                quat)
        else:
            try:
                normal = planeN.normalise()
                quat = Quat(normal)
            except ZeroDivisionError:
                quat = Quat(planeN)  # will fail on assert below:
            result = Transform3.__new__(cls, [quat, quat])
            assert result.isRefl(), \
                "normal {} doesn't define a valid 3D plane normal".format(
                    str(planeN))
        return result


class RotInv3(Transform3):
    """Define a rotary inversion"""
    def __new__(cls, qLeft=None, axis=None, angle=None):
        """
        Initialise a 3D rotation
        """
        # Do not inherit from Rot3 (and then apply inversion):
        # a rotary inversion is not a rotation.
        result = None
        if _is_quat_pair(qLeft):
            result = Transform3.__new__(cls, qLeft)
            assert result.isRotInv(), \
                "{} doesn't represent a rotary inversion".format(str(qLeft))
        else:
            ri = Rot3(qLeft, axis, angle).I()
            result = Transform3.__new__(cls, [ri[0], ri[1]])
        return result


RotRefl = RotInv3
Hx = HalfTurn3(axis=UX)
Hy = HalfTurn3(axis=UY)
Hz = HalfTurn3(axis=UZ)
I = RotInv3(Quat([1, 0, 0, 0]))
E = Rot3(Quat([1, 0, 0, 0]))


# TODO: make the 3D case a special case of 4D...
class Transform4(tuple):
    """Define a tranform in 4D"""
    def __new__(cls, quatPair):
        assert_str = "A 4D transform is represented by 2 quaternions: "
        assert len(quatPair) == 2, assert_str + str(quatPair)
        assert isinstance(quatPair[0], Quat), assert_str + str(quatPair)
        assert isinstance(quatPair[1], Quat), assert_str + str(quatPair)
        return tuple.__new__(cls, quatPair)

    def __mul__(self, u):
        """Multiply a transforms with something else

        E.g. another transform or a vector."""
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

    def angle(self):
        """return the angle of a rotation or raise NoRotation"""
        if self.isRot():
            return self._angleRot()
        # TODO: Add support for rotary inversion to Transform4
        # if self.isRotInv(): return self._angleRotInv()
        raise NoRotation(
            'oops, unknown angle; transform {}\n'.format(str(self)) +
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )

    def isRot(self):
        """Whether self represents a rotation"""
        return eq(self[0].squared_norm(), 1) and eq(self[1].squared_norm(), 1)

    def _angleRot(self):
        """Assuming the object represents a rotation, return the angle"""
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
        return 2 * math.atan2(sin, cos)


class Rot4(Transform4):
    """Define a rotation in 4D"""
    def __new__(cls,
                quatPair=None,
                axialPlane=(Vec4([0, 0, 1, 0]), Vec4([0, 0, 0, 1])),
                angle=0):
        """
        Initialise a 4D rotation
        """
        assert_str = "A 4D rotation is represented by 2 orthogonal axis: "
        assert len(axialPlane) == 2, assert_str + str(axialPlane)
        assert eq(axialPlane[0] * axialPlane[1], 0), \
            assert_str + str(axialPlane)
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
        _q0 = y * z.conjugate()
        _q1 = y.conjugate() * z
        assert eq(_q0.scalar(), 0), assert_str + str(_q0.scalar())
        assert eq(_q1.scalar(), 0), assert_str + str(_q1.scalar())
        alpha = angle / 2
        sina = math.sin(alpha)
        cosa = math.cos(alpha)
        _q0 = sina * _q0.vector()
        _q1 = sina * _q1.vector()
        return Transform4.__new__(cls,
                                  [Quat([cosa, _q0[0], _q0[1], _q0[2]]),
                                   Quat([cosa, _q1[0], _q1[1], _q1[2]])])


def find_orthogonal_plane(plane):
    """From the defined 4D plane, find the orthogonal plane"""
    # Initialise v2 so that e0 . v2 = 0 then call v2.make_orthogonal_to(e1) and
    # normalise.
    # if there is an i for which e0[i] == 0 initialising v2 is easy, just
    # define v2[i] = 1 and v2[j] = 0 for j != i
    # However v2 may not be parallel to e1.
    # If this is the case, then we can exchange the roll of e0 and e1:
    # E.G. e0 = [1/2, 1/2, 1/V2, 0] and e1 = [0, 0, 0, 1]
    # Then we would initialise v2 = [0, 0, 0, 1]
    # However v2 == e1 and it will be impossible to call
    # v2.make_orthogonal_to(e1)
    # Instead set e0 = [0, 0, 0, 1] and e1 = [1/2, 1/2, 1/V2, 0]
    # And initialise v2 = [1, 0, 0, 0] and call v2.make_orthogonal_to(e1)
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
    if zi > -1:  # if e0 contains a 0 (zero)
        v2 = unit_vec4(zi)
        if v2.is_parallel(e1):
            # exchange e0 and e1 and repeat, since we know that e1 has 3 0's
            e0, e1 = e1, e0
            status['e0_z_e1'] = 1
            zi = getZeroIndex(e0)
            if zi > -1:
                v2 = unit_vec4(zi)
                if v2.is_parallel(e1):
                    # ok, e0 had 3 zeros as well,...
                    zi = getZeroIndex(e0, zi+1)
                    if zi > -1:
                        v2 = unit_vec4(zi)
                        assert not v2.is_parallel(e1), oopsMsg
                    else:
                        assert False, oopsMsg
            else:
                assert False, oopsMsg
        status['sz_e0'] = zi
    else:
        status['sz_e0'] = 3
        zi = getZeroIndex(e1)
        if zi > -1:  # if e1 contains a 0 (zero)
            v2 = unit_vec4(zi)
            e0, e1 = e1, e0
            status['e0_z_e1'] = 2
            assert not v2.is_parallel(e1), "Ooops, this shouldn't happen!!"
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
                # Vec4([-vnIni[0],  vnIni[1], -vnIni[2],  vnIni[3]]),
                # Vec4([-vnIni[0], -vnIni[1],  vnIni[2],  vnIni[3]])
            ]
            v2Found = False
            i = -1
            while not v2Found:
                i += 1
                assert i < len(possiblePermuations), \
                    "Oops, more permutations needed"
                v2 = possiblePermuations[i]
                v2Found = not v2.is_parallel(e1)
            status['sp'] = i + 1

    # Now the plane spanned by e1 and v2 is orthogonal to e0, as a
    # consequence the following operation will keep v2 orthogonal to e0:
    e2 = v2.make_orthogonal_to(e1).normalise()

    # Use cross product for e3:
    v3 = e0.cross(e1, e2)
    # Normalisation should not be needed, but improves precision.
    # TODO
    # Prehaps this should only steered by caller by setting high precision.
    e3 = v3.normalise()
    return (e2, e3)


class DoubleRot4(Transform4):
    """Define the general (double) rotation in 4D"""
    def __new__(cls,
                quatPair=None,
                axialPlane=(Vec4([0, 0, 1, 0]), Vec4([0, 0, 0, 1])),
                angle=(0, 0)):
        orthoPlane = find_orthogonal_plane(axialPlane)
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
                    else:
                        v.append(0)
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
        # else:
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
            n_t = n.T()
            result = Mat([Vec([row * col for col in n_t]) for row in self])
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

    V = Vec([1.0, 5.0, 4.0])
    R = V[1:]
    assert R == Vec([5.0, 4.0]), 'got %s instead' % str(R)
    # TODO: howto without using deprecated __setslice__ ?
    # currently no problem, since R + W becomes a Vec anyway,
    # though 3 * R gives unexpected result
    # assert type(R) == type(Vec([]))

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
    assert R == QUARTER_TURN, 'got %s instead' % str(R)

    V = Vec([0, 10, 0])
    W = Vec([0, 3, 3])
    R = V.angle(W)
    assert R == math.pi/4, 'got %s instead' % str(R)

    V = Vec([0, 10, 0])
    W = Vec([0, -3, 0])
    R = V.angle(W)
    assert R == HALF_TURN, 'got %s instead' % str(R)

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
    Q0 = Quat([1, 2, 3, 5])
    EXP = Quat([2, 4, 6, 10])
    CHK = Q0 * 2
    assert CHK == EXP, 'got {} instead of {}'.format(str(R), EXP)
    CHK = Q0 * 2.0
    assert CHK == EXP, 'got {} instead of {}'.format(str(R), EXP)

    Q0 = Quat([1, 2, 3, 5])
    Q1 = Quat([2, 4, 3, 5])
    R = Q0 * Q1
    assert R == Quat([-40, 8, 19, 9]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    Q0 = Quat([0, 0, 0, 0])
    Q1 = Quat([2, 4, 3, 5])
    R = Q0 * Q1
    assert R == Quat([0, 0, 0, 0]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    Q0 = Quat([1, 0, 0, 0])
    Q1 = Quat([2, 4, 3, 5])
    R = Q0 * Q1
    assert R == Quat([2, 4, 3, 5]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    Q0 = Quat([0, 1, 0, 0])
    Q1 = Quat([2, 4, 3, 5])
    R = Q0 * Q1
    assert R == Quat([-4, 2, -5, 3]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    Q0 = Quat([0, 0, 1, 0])
    Q1 = Quat([2, 4, 3, 5])
    R = Q0 * Q1
    assert R == Quat([-3, 5, 2, -4]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    Q0 = Quat([0, 0, 0, 1])
    Q1 = Quat([2, 4, 3, 5])
    R = Q0 * Q1
    assert R == Quat([-5, -3, 4, 2]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    Q = Quat([2, 4, 3, 5])
    R = Q.S()
    assert R == 2, 'got %s instead' % str(R)
    assert isinstance(R, float)
    R = Q.V()
    assert R == Vec3([4, 3, 5]), 'got %s instead' % str(R)
    assert isinstance(R, Vec)

    Q = Quat([2, 4, 3, 5])
    R = Q.conjugate()
    assert R == Quat([2, -4, -3, -5]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    Q = Quat([2, 0, 0, 5])
    R = Q.conjugate()
    assert R == Quat([2, 0, 0, -5]), 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    Q = Quat([0, 0, 0, 0])
    R = Q.conjugate()
    assert R == Q, 'got %s instead' % str(R)
    assert isinstance(R, Quat)

    #####################
    # Transform: Rot3
    #####################

    R = I * I
    assert I != E, "This shouldn't hold %s != %s" % (I, E)
    assert R == E, 'got %s instead' % str(R)

    Q0 = Rot3(axis=UZ, angle=0)
    Q1 = Rot3(axis=UZ, angle=2*math.pi)
    assert Q0 == Q1, "%s should = %s" % (str(Q0), str(Q1))

    Q0 = Rot3(axis=UZ, angle=math.pi)
    Q1 = Rot3(axis=UZ, angle=-math.pi)
    assert Q0 == Q1, "%s should = %s" % (str(Q0), str(Q1))

    R = Rot3(axis=Vec3([0, 0, 0]), angle=0)
    assert R[1] == Quat([1, 0, 0, 0]), 'got %s instead' % R[1]
    assert R[0] == Quat([1, 0, 0, 0]), 'got %s instead' % R[0]

    # rotation around z -axis
    # 0 degrees (+/- 360)
    Q = Rot3(axis=UZ, angle=0)
    V = Vec3(UX)
    R = Q*V
    assert R == UX, 'got %s instead' % str(R)

    # same as above but specifying the axis as a list
    Q = Rot3(axis=[0, 0, 1], angle=0)
    V = Vec3(UX)
    R = Q*V
    assert R == UX, 'got %s instead' % str(R)

    Q = Rot3(axis=UZ, angle=FULL_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == UX, 'got %s instead' % str(R)

    Q = Rot3(axis=UZ, angle=-FULL_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == UX, 'got %s instead' % str(R)

    # 90 degrees (+/- 360)
    Q = Rot3(axis=UZ, angle=QUARTER_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == UY, 'got %s instead' % str(R)

    Q = Rot3(axis=UZ, angle=QUARTER_TURN + FULL_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == UY, 'got %s instead' % str(R)

    Q = Rot3(axis=UZ, angle=QUARTER_TURN - FULL_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == UY, 'got %s instead' % str(R)

    # 180 degrees (+/- 360)
    Q = Rot3(axis=UZ, angle=HALF_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == -UX, 'got %s instead' % str(R)

    Q = Rot3(axis=UZ, angle=HALF_TURN + FULL_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == -UX, 'got %s instead' % str(R)

    Q = Rot3(axis=UZ, angle=HALF_TURN - FULL_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == -UX, 'got %s instead' % str(R)

    # -90 degrees (+/- 360)
    Q = Rot3(axis=UZ, angle=-QUARTER_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == -UY, 'got %s instead' % str(R)

    Q = Rot3(axis=UZ, angle=-QUARTER_TURN + FULL_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == -UY, 'got %s instead' % str(R)

    Q = Rot3(axis=UZ, angle=-QUARTER_TURN - FULL_TURN)
    V = Vec3(UX)
    R = Q*V
    assert R == -UY, 'got %s instead' % str(R)

    # Quadrant I
    V3_2 = math.sqrt(3) / 2
    Q = Rot3(axis=UZ, angle=math.pi/3)
    V = UX + 3*UZ
    R = Q*V
    assert R == Vec3([0.5, V3_2, 3]), 'got %s instead' % str(R)

    # Quadrant II
    Q = Rot3(axis=UZ, angle=HALF_TURN - math.pi/3)
    V = UX + 3*UZ
    R = Q*V
    assert R == Vec3([-0.5, V3_2, 3]), 'got %s instead' % str(R)

    # Quadrant III
    Q = Rot3(axis=UZ, angle=math.pi + math.pi/3)
    V = UX + 3*UZ
    R = Q*V
    assert R == Vec3([-0.5, -V3_2, 3]), 'got %s instead' % str(R)

    # Quadrant IV
    Q = Rot3(axis=UZ, angle=- math.pi/3)
    V = UX + 3*UZ
    R = Q*V
    assert R == Vec3([0.5, -V3_2, 3]), 'got %s instead' % str(R)

    # 3D Quadrant I: rotation around (1, 1, 1): don't specify normalise axis
    Q = Rot3(axis=Vec3([1, 1, 1]), angle=THIRD_TURN)
    V = Vec3([-1, 1, 1])
    R = Q*V
    assert R == Vec3([1, -1, 1]), 'got %s instead' % str(R)
    # neg angle
    Q = Rot3(axis=Vec3([1, 1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, 1, -1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    Q = Rot3(axis=-Vec3([1, 1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, -1, 1]), 'got %s instead' % str(R)
    # neg axis
    Q = Rot3(axis=-Vec3([1, 1, 1]), angle=THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, 1, -1]), 'got %s instead' % str(R)

    # 3D Quadrant II: rotation around (-1, 1, 1): don't specify normalise axis
    Q = Rot3(axis=Vec3([-1, 1, 1]), angle=THIRD_TURN)
    V = Vec3([1, 1, 1])
    R = Q*V
    assert R == Vec3([-1, 1, -1]), 'got %s instead' % str(R)
    # neg angle
    Q = Rot3(axis=Vec3([-1, 1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    Q = Rot3(axis=-Vec3([-1, 1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([-1, 1, -1]), 'got %s instead' % str(R)
    # neg axis
    Q = Rot3(axis=-Vec3([-1, 1, 1]), angle=THIRD_TURN)
    R = Q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)

    # 3D Quadrant III: rotation around (-1, 1, 1): don't specify normalise axis
    Q = Rot3(axis=Vec3([-1, -1, 1]), angle=THIRD_TURN)
    V = Vec3([1, 1, 1])
    R = Q*V
    assert R == Vec3([-1, 1, -1]), 'got %s instead' % str(R)
    # neg angle
    Q = Rot3(axis=Vec3([-1, -1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    Q = Rot3(axis=-Vec3([-1, -1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([-1, 1, -1]), 'got %s instead' % str(R)
    # neg axis
    Q = Rot3(axis=-Vec3([-1, -1, 1]), angle=THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)

    # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise axis
    Q = Rot3(axis=Vec3([1, -1, 1]), angle=THIRD_TURN)
    V = Vec3([1, 1, 1])
    R = Q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg angle
    Q = Rot3(axis=Vec3([1, -1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    Q = Rot3(axis=-Vec3([1, -1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg axis
    Q = Rot3(axis=-Vec3([1, -1, 1]), angle=THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)

    # test quat mul from above (instead of Vec3):
    # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise axis
    Q = Rot3(axis=Vec3([1, -1, 1]), angle=THIRD_TURN)
    V = Quat([0, 1, 1, 1])
    R = Q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg angle
    Q = Rot3(axis=Vec3([1, -1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)
    # neg axis, neg angle
    Q = Rot3(axis=-Vec3([1, -1, 1]), angle=-THIRD_TURN)
    R = Q*V
    assert R == Vec3([-1, -1, 1]), 'got %s instead' % str(R)
    # neg axis
    Q = Rot3(axis=-Vec3([1, -1, 1]), angle=THIRD_TURN)
    R = Q*V
    assert R == Vec3([1, -1, -1]), 'got %s instead' % str(R)

    # Axis Angle:
    V = Vec3([1, -1, 1])
    A = THIRD_TURN
    T = Rot3(axis=V, angle=A)
    RX = T.axis()
    X = V.normalise()
    RA = T.angle()
    assert (eq(RA, A) and RX == X) or (eq(RA, -A) and RX == -X), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, RX, A, X, -A, -X)
    assert T.isRot()
    assert not T.isRefl()
    assert not T.isRotInv()
    assert T.type() == T.Rot
    # neg angle
    V = Vec3([1, -1, 1])
    A = -THIRD_TURN
    T = Rot3(axis=V, angle=A)
    RX = T.axis()
    X = V.normalise()
    RA = T.angle()
    assert (eq(RA, A) and RX == X) or (eq(RA, -A) and RX == -X), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, RX, A, X, -A, -X)
    assert T.isRot()
    assert not T.isRefl()
    assert not T.isRotInv()
    assert T.type() == T.Rot
    # neg angle, neg axis
    V = Vec3([-1, 1, -1])
    A = -THIRD_TURN
    T = Rot3(axis=V, angle=A)
    RX = T.axis()
    X = V.normalise()
    RA = T.angle()
    assert (eq(RA, A) and RX == X) or (eq(RA, -A) and RX == -X), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, RX, A, X, -A, -X)
    assert T.isRot()
    assert not T.isRefl()
    assert not T.isRotInv()
    assert T.type() == T.Rot
    # neg axis
    V = Vec3([-1, 1, -1])
    A = THIRD_TURN
    T = Rot3(axis=V, angle=A)
    RX = T.axis()
    X = V.normalise()
    RA = T.angle()
    assert (eq(RA, A) and RX == X) or (eq(RA, -A) and RX == -X), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, RX, A, X, -A, -X)
    assert T.isRot()
    assert not T.isRefl()
    assert not T.isRotInv()
    assert T.type() == T.Rot
    # Q I
    V = Vec3([-1, 1, -1])
    A = math.pi/3
    T = Rot3(axis=V, angle=A)
    RX = T.axis()
    X = V.normalise()
    RA = T.angle()
    assert (eq(RA, A) and RX == X) or (eq(RA, -A) and RX == -X), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, RX, A, X, -A, -X)
    assert T.isRot()
    assert not T.isRefl()
    assert not T.isRotInv()
    assert T.type() == T.Rot
    # Q II
    V = Vec3([-1, 1, -1])
    A = math.pi - math.pi/3
    T = Rot3(axis=V, angle=A)
    RX = T.axis()
    X = V.normalise()
    RA = T.angle()
    assert (eq(RA, A) and RX == X) or (eq(RA, -A) and RX == -X), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, RX, A, X, -A, -X)
    assert T.isRot()
    assert not T.isRefl()
    assert not T.isRotInv()
    assert T.type() == T.Rot
    # Q III
    V = Vec3([-1, 1, -1])
    A = math.pi + math.pi/3
    T = Rot3(axis=V, angle=A)
    RX = T.axis()
    X = V.normalise()
    RA = T.angle()
    A = A - 2 * math.pi
    assert (eq(RA, A) and RX == X) or (eq(RA, -A) and RX == -X), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, RX, A, X, -A, -X)
    assert T.isRot()
    assert not T.isRefl()
    assert not T.isRotInv()
    assert T.type() == T.Rot
    # Q IV
    V = Vec3([-1, 1, -1])
    A = - math.pi/3
    T = Rot3(axis=V, angle=A)
    RX = T.axis()
    X = V.normalise()
    RA = T.angle()
    assert (eq(RA, A) and RX == X) or (eq(RA, -A) and RX == -X), \
        'got ({}, {}) instead of ({}, {}) or ({}, {})'.format(
            RA, RX, A, X, -A, -X)
    assert T.isRot()
    assert not T.isRefl()
    assert not T.isRotInv()
    assert T.type() == T.Rot

    try:
        Q = Quat([2, 1, 1, 1])
        Rot3(Q)
        assert False
    except AssertionError:
        pass

    try:
        Q = Quat([-1.1, 1, 1, 1])
        Rot3(Q)
        assert False
    except AssertionError:
        pass

    try:
        Q = Quat([0, 0, 0, 0])
        Rot3(Q)
        assert False
    except AssertionError:
        pass

    # test equality for negative axis and negative angle
    R0 = Rot3(axis=Vec3([1, 2, 3]), angle=2)
    R1 = Rot3(-R0[0])
    assert R0 == R1

    # test order
    R0 = Rot3(axis=UZ, angle=QUARTER_TURN)
    R1 = Rot3(axis=UX, angle=QUARTER_TURN)
    R = (R1 * R0) * UX  # expected: R1(R0(X))
    assert R == UZ, 'Expected: %s, got %s' % (UZ, R)
    R = (R1 * R0)
    X = Rot3(axis=Vec3([1, -1, 1]), angle=THIRD_TURN)
    assert R == X, 'Expected: %s, got %s' % (X, R)
    R = (R0 * R1)
    X = Rot3(axis=Vec3([1, 1, 1]), angle=THIRD_TURN)
    assert R == X, 'Expected: %s, got %s' % (X, R)

    # test conversion to Mat
    # x-axis
    R = Rot3(axis=UZ, angle=QUARTER_TURN).matrix()
    # 0  -1  0
    # 1   0  0
    # 0   0  1
    X = Vec3([0, -1, 0])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([1, 0, 0])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([0, 0, 1])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])
    R = Rot3(axis=UZ, angle=HALF_TURN).matrix()
    # -1   0  0
    #  0  -1  0
    #  0   0  1
    X = Vec3([-1, 0, 0])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([0, -1, 0])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([0, 0, 1])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])
    R = Rot3(axis=UZ, angle=-QUARTER_TURN).matrix()
    #  0   1  0
    # -1   0  0
    #  0   0  1
    X = Vec3([0, 1, 0])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([-1, 0, 0])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([0, 0, 1])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])

    # y-axis
    R = Rot3(axis=UY, angle=QUARTER_TURN).matrix()
    #  0   0   1
    #  0   1   0
    # -1   0   0
    X = Vec3([0, 0, 1])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([0, 1, 0])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([-1, 0, 0])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])
    R = Rot3(axis=UY, angle=HALF_TURN).matrix()
    # -1   0   0
    #  0   1   0
    #  0   0  -1
    X = Vec3([-1, 0, 0])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([0, 1, 0])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([0, 0, -1])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])
    R = Rot3(axis=UY, angle=-QUARTER_TURN).matrix()
    #  0   0  -1
    #  0   1   0
    #  1   0   0
    X = Vec3([0, 0, -1])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([0, 1, 0])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([1, 0, 0])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])

    # x-axis
    R = Rot3(axis=UX, angle=QUARTER_TURN).matrix()
    # 1  0  0
    # 0  0 -1
    # 0  1  0
    X = Vec3([1, 0, 0])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([0, 0, -1])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([0, 1, 0])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])
    R = Rot3(axis=UX, angle=HALF_TURN).matrix()
    #  1  0  0
    #  0 -1  0
    #  0  0 -1
    X = Vec3([1, 0, 0])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([0, -1, 0])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([0, 0, -1])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])
    R = Rot3(axis=UX, angle=-QUARTER_TURN).matrix()
    #  1  0  0
    #  0  0  1
    #  0 -1  0
    X = Vec3([1, 0, 0])
    assert R[0] == X, 'Expected: %s, got %s' % (X, R[0])
    X = Vec3([0, 0, 1])
    assert R[1] == X, 'Expected: %s, got %s' % (X, R[1])
    X = Vec3([0, -1, 0])
    assert R[2] == X, 'Expected: %s, got %s' % (X, R[2])

    seed(700114)  # constant seed to be able to catch errors
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
        Q = Quat([0, 0, 0, 0])
        Refl3(Q)
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

    seed(700114)  # constant seed to be able to catch errors
    for K in range(100):
        S0 = Refl3(planeN=Vec3([2*random()-1, 2*random()-1, 2*random()-1]))
        S1 = Refl3(planeN=Vec3([2*random()-1, 2*random()-1, 2*random()-1]))
        R = S0 * S1
        assert not S0.isRot()
        assert S0.isRefl()
        assert not S0.isRotInv(), "for i = %d: %s" % (K, str(S0))
        assert not S1.isRot()
        assert S1.isRefl()
        assert not S1.isRotInv()
        assert R.isRot()
        assert not R.isRefl()
        assert not R.isRotInv()
        assert (S0 * S0) == E, 'for i == %d' % K
        assert (S1 * S1) == E, 'for i == %d' % K
        assert R * R.inverse() == E

    # border cases
    S0 = Refl3(planeN=UX)
    S1 = Refl3(planeN=UY)
    R = S0 * S1
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(axis=UZ)
    R = S1 * S0
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(axis=UZ)

    S0 = Refl3(planeN=UX)
    S1 = Refl3(planeN=UZ)
    R = S0 * S1
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(axis=UY)
    R = S1 * S0
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(axis=UY)

    S0 = Refl3(planeN=UY)
    S1 = Refl3(planeN=UZ)
    R = S0 * S1
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(axis=UX)
    R = S1 * S0
    assert R.isRot()
    assert not R.isRefl()
    assert not R.isRotInv()
    assert R == HalfTurn3(axis=UX)

    S0 = Refl3(planeN=UX)
    S1 = Refl3(planeN=UY)
    S2 = Refl3(planeN=UZ)
    R = S0 * S1 * S2
    assert not R.isRot()
    assert not R.isRefl()
    assert R.isRotInv()
    assert R.isRotRefl()
    assert R == I

    # test order: 2 refl planes with 45 degrees in between: 90 rotation
    S0 = Refl3(planeN=Vec3([0, 3, 0]))
    S1 = Refl3(planeN=Vec3([-1, 1, 0]))
    R = (S1 * S0)
    X = Rot3(axis=UZ, angle=QUARTER_TURN)
    assert R == X, 'Expected: %s, got %s' % (X, R)
    R = (S0 * S1)
    X = Rot3(axis=UZ, angle=-QUARTER_TURN)
    assert R == X, 'Expected: %s, got %s' % (X, R)

    # tests eq reflection for opposite normals
    seed(760117)  # constant seed to be able to catch errors
    for K in range(100):
        N = Vec3([2*random()-1, 2*random()-1, 2*random()-1])
        S0 = Refl3(planeN=N)
        S1 = Refl3(planeN=-N)
        assert S0 == S1, '{} should == {} (i={})'.format(S0, S1, K)
        R = S0 * S1
        assert R == E, 'refl*refl: {} should == {} (i={})'.format(R, E, K)

    # reflection in same plane: border cases
    BORDER_CASES = [UX, UY, UZ]
    for N in BORDER_CASES:
        S0 = Refl3(planeN=N)
        S1 = Refl3(planeN=-N)
        assert S0 == S1, '{} should == {} (i={})'.format(S0, S1, N)
        R = S0 * S1
        assert R == E, 'refl*refl: {} should == {} (i={})'.format(R, E, N)

    #####################
    # Transform: Rotary inversion
    #####################

    # type: R*I == I*R and gives a rotary inversion (random)

    seed(700114)  # constant seed to be able to catch errors
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
    X = Quat([V[0], 1, -math.sqrt(3), V[3]])
    set_eq_float_margin(1.0e-14)
    assert R == X, 'Expected: %s, got %s' % (X, R)

    seed(700114)  # constant seed to be able to catch errors
    for K in range(100):
        x0 = Vec4([2*random()-1, 2*random()-1, 2*random()-1, 2*random()-1])
        # make sure orthogonal: x0*x1 + y0*y1 + z0*z1 + w0*w1 == 0
        W, X, Y = (2*random()-1, 2*random()-1, 2*random()-1)
        Z = (-W * x0[0] - X * x0[1] - Y * x0[2]) / x0[3]
        x1 = Vec4([W, X, Y, Z])
        R0 = Rot4(axialPlane=(x0, x1), angle=random() * 2 * math.pi)
        x0 = Vec4([2*random()-1, 2*random()-1, 2*random()-1, 2*random()-1])
        W, X, Y = (2*random()-1, 2*random()-1, 2*random()-1)
        # make sure orthogonal: x0*x1 + y0*y1 + z0*z1 + w0*w1 == 0
        Z = (-W * x0[0] - X * x0[1] - Y * x0[2]) / x0[3]
        x1 = Vec4([W, X, Y, Z])
        R1 = Rot4(axialPlane=(x0, x1), angle=random() * 2 * math.pi)
        R = R0 * R1
        assert R0.isRot()
        # Check these as soon as they are implemented for Transform4
        # assert not R0.isRefl()
        # assert not R0.isRotInv()
        assert R1.isRot()
        # assert not R1.isRefl()
        # assert not R1.isRotInv()
        assert R.isRot()
        # assert not R.isRefl()
        # assert not R.isRotInv()
        # assert R0 * R0.inverse() == E
        # assert R1 * R1.inverse() == E
        # assert R * R.inverse() == E
        for N in range(1, 12):
            if N > 98:
                MARGIN = 1.0e-12
            else:
                MARGIN = DEFAULT_EQ_FLOAT_MARGIN
            R0 = Rot4(axialPlane=(x0, x1), angle=2 * math.pi / N)
            R = R0
            for J in range(1, N):
                A = R.angle()
                assert eq(J * 2 * math.pi / N, A, MARGIN), \
                    'j: {}, R: {}'.format(J, 2 * math.pi / N / A)
                R = R0 * R
            RA = R.angle()
            assert eq(RA, 0, MARGIN) or eq(RA, 2*math.pi, MARGIN), R.angle()

    #####################
    # DoubleRot4:
    #####################
    R0 = DoubleRot4(axialPlane=(Vec4([1, 0, 0, 0]), Vec4([0, 0, 0, 1])),
                    # 1/6 th and 1/8 th turn
                    angle=(math.pi/3, math.pi/4))
    V = Vec4([6, 2, 0, 6])
    R = R0 * V
    X = Quat([0, 1, -math.sqrt(3), math.sqrt(72)])
    MARGIN = 1.0e-14
    assert R0.isRot()
    assert R == X, 'Expected: %s, got %s' % (X, R)
    R = E
    for K in range(23):
        R = R0 * R
        OOPS_MSG = 'oops for i = {}'.format(K)
        assert R.isRot(), OOPS_MSG
        RA = R.angle()
        assert not eq(RA, 0, MARGIN) and not eq(RA, 2*math.pi, MARGIN), RA
    R = R0 * R
    assert R.isRot()
    RA = R.angle()
    assert eq(RA, 0, MARGIN) or eq(RA, 2*math.pi, MARGIN), R.angle()

    R0 = DoubleRot4(axialPlane=(Vec4([1, 0, 0, 0]), Vec4([0, 0, 0, 1])),
                    # 1/6 th and 1/8 th turn:
                    angle=(math.pi/4, math.pi/3))
    V = Vec4([6, 2, 2, 0])
    R = R0 * V
    X = Quat([3, math.sqrt(8), 0, 3*math.sqrt(3)])
    MARGIN = 1.0e-14
    assert R0.isRot()
    assert R == X, 'Expected: %s, got %s' % (X, R)
    R = E
    for K in range(23):
        R = R0 * R
        OOPS_MSG = 'oops for i = {}'.format(K)
        assert R.isRot(), OOPS_MSG
        RA = R.angle()
        assert not eq(RA, 0, MARGIN) and not eq(RA, 2*math.pi, MARGIN), RA
    R = R0 * R
    assert R.isRot()
    RA = R.angle()
    assert eq(RA, 0, MARGIN) or eq(RA, 2*math.pi, MARGIN), R.angle()

    # test if vectors in axial plane are not changed.
    V0 = Vec4([1, 1, 1, 0])
    V1 = Vec4([0, 0, 1, 1])
    V1 = V1.make_orthogonal_to(V0)
    R0 = DoubleRot4(axialPlane=(V1, V0),
                    # 1/6 th and 1/8 th turn:
                    angle=(math.pi/4, math.pi/3))
    for K in range(5):
        V = V0 + K * V1
        R = R0 * V
        X = V
        assert eq(RA, 0, MARGIN) or eq(RA, 2*math.pi, MARGIN), \
            "{}: expected: {}, got: {}".format(K, X, R)
        V = K * V0 + V1
        R = R0 * V
        X = V
        assert eq(RA, 0, MARGIN) or eq(RA, 2*math.pi, MARGIN), \
            "{}: expected: {}, got: {}".format(K, X, R)

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

    print('All tests passed')
