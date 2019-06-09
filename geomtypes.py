#!/usr/bin/python
"""
Module with geometrical types.
"""
#
# Copyright (C) 2010-2019 Marcel Tunnissen
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
# pylint: disable=too-many-lines,too-many-branches

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
        vec_str = "["
        if self:
            vec_str += float2str(self[0], DEFAULT_ROUND_FLOAT_MARGIN)
            for e in self[1:]:
                vec_str += ', {}'.format(float2str(e,
                                                   DEFAULT_ROUND_FLOAT_MARGIN))
        vec_str += "]"
        s = indent.Str('{}({})'.format(self.__class__.__name__, vec_str))
        if __name__ != '__main__':
            s = s.insert('{}.'.format(__name__))
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
        self._cache = {}

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
        if 'vector_part' not in self._cache:
            self._cache['vector_part'] = Vec3(self[1:])
        return self._cache['vector_part']

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
        self._cache = {}

    def __repr__(self):
        s = indent.Str('%s((\n' % (_transform3_type_str(self.type())))
        s = s.add_incr_line('%s,' % repr(Quat(self[0])))
        s = s.add_line('%s,' % repr(Quat(self[1])))
        s = s.add_decr_line('))')
        if __name__ != '__main__':
            s = s.insert('%s.' % __name__)
        return s

    def __hash__(self):
        if 'hash_nr' not in self._cache:
            if self.is_rot():
                self._cache['hash_nr'] = self.__hash_rot()
            elif self.is_refl():
                self._cache['hash_nr'] = self.__has_refl()
            elif self.is_rot_inv():
                self._cache['hash_nr'] = self.__hash_rot_inv()
            else:
                raise UnsupportedTransform("Not a (supported) transform")
        return self._cache['hash_nr']

    def __str__(self):
        if self.is_rot():
            return self.__str_rot()
        if self.is_refl():
            return self.__str_refl()
        if self.is_rot_inv():
            return self.__str_rot_inv()
        # non-proper transform: show the quaternion pair.
        return '%s * .. * %s' % (str(self[0]), str(self[1]))

    def to_orbit_str(self, prec=DEFAULT_ROUND_FLOAT_MARGIN):
        """Return the orbit file format representation for this transform.

        If this is not a proper transform, then UnsupportedTransform is raised
        """
        if self.is_rot():
            return self.__rot2orbit(prec)
        if self.is_refl():
            return self.__refl2orbit(prec)
        if self.is_rot_inv():
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
        if self.is_rot() and u.is_rot():
            is_eq = self.__eq_rot(u)
        elif self.is_refl() and u.is_refl():
            is_eq = self.__eq_refl(u)
        elif self.is_rot_inv() and u.is_rot_inv():
            is_eq = self._eq_rot_inv(u)
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
        if self.is_rot():
            return self.Rot
        if self.is_refl():
            return self.Refl
        if self.is_rot_inv():
            return self.RotInv
        raise UnsupportedTransform(
            "Not a (supported) transform: {} != 1?".format(self[1].norm()))

    def angle(self):
        """In case this transform contains a rotation, return the angle

        Otherwise raise a NoRotation exception

        The angle is returned in radians.

        If the transform is a rotary inversion, which is the same as an rotary
        reflection, then the angle for the rotary inversion is returned. If you
        want to know the angle for the rotary reflection, you can either call
        angle_rot_refl or subtract a halft turn.
        """
        if self.is_rot():
            return self.__angle_rot()
        if self.is_rot_inv():
            return self.__angle_rot_inv()
        raise NoRotation(
            'oops, unknown angle; transform {}\n'.format(str(self)) +
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )

    def axis(self):
        """In case this transform contains a rotation, return the axis

        Otherwise raise a NoRotation exception
        """
        if self.is_rot():
            return self.__axis_rot()
        if self.is_rot_inv():
            return self.__axis_rot_inv()
        raise NoRotation(
            'oops, unknown axis; transform {}\n'.format(str(self)) +
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )

    def glMatrix(self):
        """Return the glMatrix representation of this transform"""
        if self.is_rot():
            m = self.__glMatrix_rot()
        elif self.is_refl():
            m = self.__matrix_refl()
        elif self.is_rot_inv():
            m = self.__glMatrix_rot_inv()
        else:
            raise UnsupportedTransform(
                'oops, unknown matrix; transform {}\n'.format(str(self)))
        return Mat([Vec([m[0][0], m[0][1], m[0][2], 0]),
                    Vec([m[1][0], m[1][1], m[1][2], 0]),
                    Vec([m[2][0], m[2][1], m[2][2], 0]),
                    Vec([0, 0, 0, 1])])

    def matrix(self):
        """Return the matrix representation of this transform"""
        if self.is_rot():
            return self.__matrix_rot()
        if self.is_refl():
            return self.__matrix_refl()
        if self.is_rot_inv():
            return self.__matrix_rot_inv()
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
        if self.is_rot():
            return self.__inverse_rot()
        if self.is_refl():
            return self.__inverse_refl()
        if self.is_rot_inv():
            return self.__inverse_rot_inv()
        raise UnsupportedTransform(
            'oops, unknown matrix; transform {}\n'.format(str(self)))

    def is_direct(self):
        """Return whether this is an opposite transform (i.e. not direct)"""
        return self.is_rot()

    def is_opposite(self):
        """Return whether this is an opposite transform (i.e. not direct)"""
        return not self.is_direct()

    # *** ROTATION specific functions:
    def is_rot(self):
        """Return whether this tranform is a rotation."""
        d = 1 - self.eq_float_margin
        _margin = 1 - d * d
        eq_square_norm = eq(self[1].squared_norm(), 1, margin=_margin)
        return (
            self[1].conjugate() == self[0]
            and
            eq_square_norm
            and
            (self[1].S() < 1 or eq(self[1].S(), 1))
            and
            (self[1].S() > -1 or eq(self[1].S(), -1))
        )

    def __eq_rot(self, u):
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

    def __hash_rot(self):
        axis = self.__axis_rot()
        return hash((self.Rot,
                     round(self.__angle_rot(), DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[0], DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[1], DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[2], DEFAULT_ROUND_FLOAT_MARGIN)))

    def __str_rot(self):
        axis = self.__axis_rot()
        return 'Rotation of {} degrees around [{}, {}, {}]'.format(
            float2str(
                to_degrees(self.__angle_rot()), DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[0], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[1], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(axis[2], DEFAULT_ROUND_FLOAT_MARGIN))

    def __rot2orbit(self, prec=DEFAULT_ROUND_FLOAT_MARGIN):
        axis = self.__axis_rot()
        return 'R {} {} {} {}'.format(
            float2str(self.__angle_rot(), prec),
            float2str(axis[0], prec),
            float2str(axis[1], prec),
            float2str(axis[2], prec))

    def __angle_rot(self):
        if 'angleRot' not in self._cache:
            self._define_unique_angle_axis()
        return self._cache['angleRot']

    def __axis_rot(self):
        if 'axisRot' not in self._cache:
            self._define_unique_angle_axis()
        return self._cache['axisRot']

    def _define_unique_angle_axis(self):
        # rotation axis
        try:
            self._cache['axisRot'] = self[0].V().normalise()
        except ZeroDivisionError:
            assert self[0] == Quat([1, 0, 0, 0]) or \
                self[0] == Quat([-1, 0, 0, 0]), \
                "{} doesn'self represent a rotation".format(self.__repr__())
            self._cache['axisRot'] = self[0].V()
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
        self._cache['angleRot'] = 2 * math.atan2(sin, cos)

        # make unique: -pi < angle < pi
        if not (self._cache['angleRot'] < math.pi
                or eq(self._cache['angleRot'], math.pi)):
            self._cache['angleRot'] = self._cache['angleRot'] - \
                2 * math.pi
        if not (self._cache['angleRot'] > -math.pi
                or eq(self._cache['angleRot'], -math.pi)):
            self._cache['angleRot'] = self._cache['angleRot'] + \
                2 * math.pi

        # make unique: 0 < angle < pi
        if eq(self._cache['angleRot'], 0):
            self._cache['angleRot'] = 0.0
        if self._cache['angleRot'] < 0:
            self._cache['angleRot'] = -self._cache['angleRot']
            self._cache['axisRot'] = -self._cache['axisRot']
        if eq(self._cache['angleRot'], math.pi):
            # if halfturn, make axis unique: make the first non-zero element
            # positive:
            if eq(self._cache['axisRot'][0], 0):
                self._cache['axisRot'] = Vec3(
                    [0.0,
                     self._cache['axisRot'][1],
                     self._cache['axisRot'][2]])
            if self._cache['axisRot'][0] < 0:
                self._cache['axisRot'] = -self._cache['axisRot']
            elif self._cache['axisRot'][0] == 0:
                if eq(self._cache['axisRot'][1], 0):
                    self._cache['axisRot'] = Vec3(
                        [0.0, 0.0, self._cache['axisRot'][2]])
                if self._cache['axisRot'][1] < 0:
                    self._cache['axisRot'] = -self._cache['axisRot']
                elif self._cache['axisRot'][1] == 0:
                    # not valid axis: if eq(self._cache['axisRot'][2], 0):
                    if self._cache['axisRot'][2] < 0:
                        self._cache['axisRot'] = -self._cache['axisRot']
        elif eq(self._cache['angleRot'], 0):
            self._cache['angleRot'] = 0.0
            self._cache['axisRot'] = Vec3([1.0, 0.0, 0.0])

    def __matrix_rot(self):
        if 'matrix_rot' not in self._cache:
            w, x, y, z = self[0]
            self._cache['matrix_rot'] = _get_mat_rot(w, x, y, z)
        return self._cache['matrix_rot']

    def __glMatrix_rot(self):
        if 'gl_matrix_rot' not in self._cache:
            w, x, y, z = self[0]
            self._cache['gl_matrix_rot'] = _get_mat_rot(-w, x, y, z)
        return self._cache['gl_matrix_rot']

    def __inverse_rot(self):
        if 'inverse_rot' not in self._cache:
            self._cache['inverse_rot'] = Rot3(axis=self.axis(),
                                              angle=-self.angle())
        return self._cache['inverse_rot']

    # *** REFLECTION specific functions:
    def is_refl(self):
        """Return whether this tranform is a reflection."""
        return (
            self[1] == self[0]
            and
            eq(self[1].squared_norm(), 1)
            and
            eq(self[1].S(), 0)
        )

    def __eq_refl(self, u):
        """Compare two transforms that represent reflections"""
        # not needed: and self[1] == u[1]
        # since __eq_refl is called for self and u reflections
        return (self[0] == u[0]) or (self[0] == -u[0])

    def __has_refl(self):
        normal = self.plane_normal()
        return hash(
            (
                self.Refl,
                self.Refl,  # to use a tuple of 5 elements for all types
                round(normal[0], DEFAULT_ROUND_FLOAT_MARGIN),
                round(normal[1], DEFAULT_ROUND_FLOAT_MARGIN),
                round(normal[2], DEFAULT_ROUND_FLOAT_MARGIN)
            )
        )

    def __str_refl(self):
        norm = self.plane_normal()
        return 'Reflection in plane with normal [{}, {}, {}]'.format(
            float2str(norm[0], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(norm[1], DEFAULT_ROUND_FLOAT_MARGIN),
            float2str(norm[2], DEFAULT_ROUND_FLOAT_MARGIN))

    def __refl2orbit(self, prec=DEFAULT_ROUND_FLOAT_MARGIN):
        norm = self.plane_normal()
        return 'S {} {} {}'.format(
            float2str(norm[0], prec),
            float2str(norm[1], prec),
            float2str(norm[2], prec))

    def plane_normal(self):
        """If this is a reflection, return the plane normal.

        Should only be called when this is a reflection.
        """
        if 'plane_normal' not in self._cache:
            self._cache['plane_normal'] = self[0].V()
            # make normal unique: make the first non-zero element positive:
            if eq(self._cache['plane_normal'][0], 0):
                self._cache['plane_normal'] = Vec3(
                    [0.0,
                     self._cache['plane_normal'][1],
                     self._cache['plane_normal'][2]])
            if self._cache['plane_normal'][0] < 0:
                self._cache['plane_normal'] = -self._cache[
                    'plane_normal']
            elif self._cache['plane_normal'][0] == 0:
                if eq(self._cache['plane_normal'][1], 0):
                    self._cache['plane_normal'] = Vec3(
                        [0.0, 0.0, self._cache['plane_normal'][2]])
                if self._cache['plane_normal'][1] < 0:
                    self._cache['plane_normal'] = -self._cache[
                        'plane_normal']
                elif self._cache['plane_normal'][1] == 0:
                    # not needed (since not valid axis):
                    # if eq(self._cache['plane_normal'][2], 0):
                    if self._cache['plane_normal'][2] < 0:
                        self._cache['plane_normal'] = -self._cache[
                            'plane_normal']
        return self._cache['plane_normal']

    def __matrix_refl(self):
        if 'matrix_refl' not in self._cache:
            _, x, y, z = self[0]
            dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
            dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
            self._cache['matrix_refl'] = [
                Vec([1-dx2, -dxy, -dxz]),
                Vec([-dxy, 1-dy2, -dyz]),
                Vec([-dxz, -dyz, 1-dz2]),
            ]
        return self._cache['matrix_refl']

    def __inverse_refl(self):
        return self

    # *** ROTARY INVERSION (= ROTARY RELECTION) specific functions:
    def I(self):
        """Apply a central inversion on this transform."""
        if 'central_inverted' not in self._cache:
            self._cache['central_inverted'] = Transform3(
                [-self[0], self[1]])
        return self._cache['central_inverted']

    def is_rot_inv(self):
        """Return whether the transform is a rotary inversion."""
        return self.I().is_rot() and not self.is_refl()

    def _eq_rot_inv(self, u):
        return self.I() == u.I()

    def __hash_rot_inv(self):
        axis = self.__axis_rot_inv()
        return hash((self.Rot,
                     round(self.__angle_rot_inv(), DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[0], DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[1], DEFAULT_ROUND_FLOAT_MARGIN),
                     round(axis[2], DEFAULT_ROUND_FLOAT_MARGIN)))

    def __str_rot_inv(self):
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

    def __angle_rot_inv(self):
        """If this is a rotary inversion, return the angle.

        Make sure to only call this method when this is a rotary inversion
        """
        return self.I().angle()

    def __axis_rot_inv(self):
        """If this is a rotary inversion, return the axis.

        Make sure to only call this method when this is a rotary inversion
        """
        return self.I().axis()

    def __matrix_rot_inv(self):
        """If this is a rotary inversion, return the matrix representation.

        Should only be called when this is a rotary inversion
        """
        if 'matrix_rot_inv' not in self._cache:
            w, x, y, z = self[0]
            self._cache['matrix_rot_inv'] = _get_mat_rot(w, x, y, z, -1)
        return self._cache['matrix_rot_inv']

    def __glMatrix_rot_inv(self):
        """If this is a rotary inversion, return the glMatrix.

        Should only be called when this is a rotary inversion
        """
        if 'gl_matrix_rot_inv' not in self._cache:
            w, x, y, z = self[0]
            self._cache['gl_matrix_rot_inv'] = _get_mat_rot(-w, x, y, z, -1)
        return self._cache['gl_matrix_rot_inv']

    def __inverse_rot_inv(self):
        """If this is a rotary inversion, return the reverse.

        Should only be called when this is a rotary inversion
        """
        if 'inverse_rot_inv' not in self._cache:
            self._cache['inverse_rot_inv'] = RotInv3(axis=self.axis(),
                                                     angle=-self.angle())
        return self._cache['inverse_rot_inv']

    is_rot_refl = is_rot_inv
    # not needed: since they are the same (you can use the axis method):
    # axis_rot_refl = __axis_rot_inv

    def angle_rot_refl(self):
        """Return the angle of a rotary reflection.

        A public method is provided in case one prefers to use rotary
        reflections instead of rotary inversion. These transforms are the same,
        but they differ in angle, i.e. the standard method angle cannot be
        used.
        """
        return self.__angle_rot_inv() - HALF_TURN


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
            if not trans.is_rot():
                raise NoRotation("{} doesn't represent a rotation".format(
                    str(quat)))
            return trans
        elif isinstance(quat, Quat):
            try:
                quat = quat.normalise()
            except ZeroDivisionError:
                pass  # raise exception below
            trans = Transform3.__new__(cls, [quat, quat.conjugate()])
            if not trans.is_rot():
                raise NoRotation("{} doesn't represent a rotation".format(
                    str(quat)))
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
    def __new__(cls, quat=None, normal=None):
        """Define a 3D reflection is a plane

        Either define
        quat: quaternion representing the left (and right) quaternion
        multiplication for a reflection
        or
        normal: the 3D normal of the plane in which the reflection takes place.
        """
        result = None
        if _is_quat_pair(quat):
            result = Transform3.__new__(cls, quat)
            assert result.is_refl(), "%s doesn't represent a reflection" % str(
                quat)
        elif isinstance(quat, Quat):
            try:
                quat = quat.normalise()
            except ZeroDivisionError:
                pass  # will fail on assert below:
            result = Transform3.__new__(cls, [quat, quat])
            assert result.is_refl(), "%s doesn't represent a reflection" % str(
                quat)
        else:
            try:
                normal = normal.normalise()
                quat = Quat(normal)
            except ZeroDivisionError:
                quat = Quat(normal)  # will fail on assert below:
            result = Transform3.__new__(cls, [quat, quat])
            assert result.is_refl(), \
                "normal {} doesn't define a valid 3D plane normal".format(
                    str(normal))
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
            assert result.is_rot_inv(), \
                "{} doesn't represent a rotary inversion".format(str(qLeft))
        else:
            ri = Rot3(qLeft, axis, angle).I()
            result = Transform3.__new__(cls, [ri[0], ri[1]])
        return result


RotRefl = RotInv3
HX = HalfTurn3(axis=UX)
HY = HalfTurn3(axis=UY)
HZ = HalfTurn3(axis=UZ)
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
        if self.is_rot():
            return self.__angle_rot()
        # TODO: Add support for rotary inversion to Transform4
        # if self.is_rot_inv(): return self.__angle_rot_inv()
        raise NoRotation(
            'oops, unknown angle; transform {}\n'.format(str(self)) +
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )

    def is_rot(self):
        """Whether self represents a rotation"""
        return eq(self[0].squared_norm(), 1) and eq(self[1].squared_norm(), 1)

    def __angle_rot(self):
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
    def get_zero_index(v, s=0):
        """
        Get the index of the element that equals to 0 in vec v. If there
        none, -1 is returned.

        s: start with (incl) position s
        """
        zero_index = -1
        for i in range(s, 4):
            if eq(v[i], 0):
                zero_index = i
                break
        return zero_index

    oops_msg = "Ooops, this shouldn't happen!!"

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
    zi = get_zero_index(e0)
    if zi > -1:  # if e0 contains a 0 (zero)
        v2 = unit_vec4(zi)
        if v2.is_parallel(e1):
            # exchange e0 and e1 and repeat, since we know that e1 has 3 0's
            e0, e1 = e1, e0
            status['e0_z_e1'] = 1
            zi = get_zero_index(e0)
            if zi > -1:
                v2 = unit_vec4(zi)
                if v2.is_parallel(e1):
                    # ok, e0 had 3 zeros as well,...
                    zi = get_zero_index(e0, zi+1)
                    if zi > -1:
                        v2 = unit_vec4(zi)
                        assert not v2.is_parallel(e1), oops_msg
                    else:
                        assert False, oops_msg
            else:
                assert False, oops_msg
        status['sz_e0'] = zi
    else:
        status['sz_e0'] = 3
        zi = get_zero_index(e1)
        if zi > -1:  # if e1 contains a 0 (zero)
            v2 = unit_vec4(zi)
            e0, e1 = e1, e0
            status['e0_z_e1'] = 2
            assert not v2.is_parallel(e1), "Ooops, this shouldn't happen!!"
            status['sz_e1'] = zi
        else:
            vn_ini = Vec4([1/e0[0], 1/e0[1], 1/e0[2], 1/e0[3]])
            possible_permutations = [
                Vec4([vn_ini[0], vn_ini[1], -vn_ini[2], -vn_ini[3]]),
                Vec4([vn_ini[0], -vn_ini[1], vn_ini[2], -vn_ini[3]]),
                Vec4([-vn_ini[0], vn_ini[1], vn_ini[2], -vn_ini[3]]),
                # this might be used later for e3:
                Vec4([vn_ini[0], -vn_ini[1], -vn_ini[2], vn_ini[3]]),
                # I don't think these are necessary:
                # Vec4([-vn_ini[0],  vn_ini[1], -vn_ini[2],  vn_ini[3]]),
                # Vec4([-vn_ini[0], -vn_ini[1],  vn_ini[2],  vn_ini[3]])
            ]
            v2_found = False
            i = -1
            while not v2_found:
                i += 1
                assert i < len(possible_permutations), \
                    "Oops, more permutations needed"
                v2 = possible_permutations[i]
                v2_found = not v2.is_parallel(e1)
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
        ortho_plane = find_orthogonal_plane(axialPlane)
        r0 = Rot4(axialPlane=axialPlane, angle=angle[0])
        r1 = Rot4(axialPlane=ortho_plane, angle=angle[1])
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

    def rm_row(self, i):
        """Delete row i"""
        # don't use self.pop(i), it changes self, while the result should be
        # returned instead.
        if i < 0:
            i += self.rows
        assert i >= 0
        n = self[0:i]
        n.extend(self[i+1:])
        return Mat(n)

    def rm_col(self, i):
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

    def replace_col(self, i, v):
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
        return self.rm_row(i).rm_col(j).det()

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
            [self.replace_col(i, v).det() / det for i in range(self.cols)])
