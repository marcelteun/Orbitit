#!/usr/bin/env python
"""
Module with geometrical types.
"""
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
# Old sins:
# pylint: disable=too-many-lines,too-many-branches


from __future__ import annotations
import json
import logging
import math
from typing import overload

from orbitit import base, indent
from orbitit.base import Singleton  # to prevent pylint (2.4.4): Undefined variable 'base.Singleton'


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

DEFAULT_FLOAT_PRECISION = 10
FLOAT_PRECISION = DEFAULT_FLOAT_PRECISION

# Used for output: use a bit more than when comparing, to not loose when rounding.
DEFAULT_FLOAT_OUT_PRECISION = 13
FLOAT_OUT_PRECISION = DEFAULT_FLOAT_OUT_PRECISION

def f2s(f, precision=None):
    """Get string representation of a float or int with certain precision

    The floating point notation is used with a certain precision. Scientific notication is prevented
    so that the string can be used in geom_gui.FloatInput. The length of the string representation
    for the floating point number is minimised, i.e. 0.00001 with precision 4 is written as "0".

    precision: maximum amount of decimal places used for writing out the floating point number.
    """
    if not precision:
        precision = DEFAULT_FLOAT_OUT_PRECISION
    fmt = f"{{:0.{precision}f}}"
    s = fmt.format(f)
    s = s.rstrip('0').rstrip('.')
    if s != '-0':
        return s
    return '0'


# TODO: move this to own module?

class StdFloatHandler(metaclass=Singleton):
    """A singleto that can be used to compare and print float with a certain precision.

    This can be used as follows:
        with StdFloatHandler()(precision=7) as fh:
            fh.eq(0.12345, 0.12346)
            print(0.12345678)
    Which will evaluate to True and print "0.1234568"

    The precision is the amount of decimals that should be looked at
    """

    def __init__(self):
        self.next_precision = FLOAT_PRECISION
        self.precisions = [FLOAT_PRECISION]
        self.margin = self.get_margin()

    @property
    def precision(self):
        """Get the current precision."""
        return self.precisions[-1]

    def get_margin(self):
        """Return the margin from the amount of digits."""
        return 1.0*10**-self.precision

    def __call__(self, precision=FLOAT_PRECISION):
        """Call the object to set the next precision to be used with the "with" statement"""
        self.next_precision = precision
        return self

    def __enter__(self):
        """Set precision to be used and calculate the margin."""
        self.precisions.append(self.next_precision)
        self.margin = self.get_margin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """go back using the previous precision and margin."""
        self.precisions.pop()
        self.margin = self.get_margin()

    def eq(self, f0, f1):  # pylint: disable=C0103
        """Check wether f0 == f1 within a margin."""
        # Note: must be float compare
        return float(abs(f0 - f1)) < self.margin

    def ne(self, f0, f1):  # pylint: disable=C0103
        """Check wether f0 == f1 within a margin."""
        return not self.eq(f0, f1)

    def lt(self, f0, f1):  # pylint: disable=C0103
        """Check wether f0 < f1 within a margin."""
        # to prevent recursion (through RoundedFloat):
        return float(f1) - float(f0) > self.margin

    def le(self, f0, f1):  # pylint: disable=C0103
        """Check wether f0 <= f1 within a margin."""
        # Note: must be float compare
        return float(f0 - f1) < self.margin

    def gt(self, f0, f1):  # pylint: disable=C0103
        """Check wether f0 > f1 within a margin."""
        # to prevent recursion (through RoundedFloat):
        return float(f0) - float(f1) > self.margin

    def ge(self, f0, f1):  # pylint: disable=C0103
        """Check wether f0 >= f1 within a margin."""
        # Note: must be float compare
        return float(f1 - f0) < self.margin

    def to_str(self, f):
        """Convert the supplied floating point to a string."""
        return f2s(f, self.precision)


# The variable below is the singleton object that can be used instead of StdFloatHandler()
# Use the following construction:
#     with FloatHandler(precision=7) as fh:
#         fh.eq(0.12345, 0.12346)
#         print(0.12345678)
# Which will evaluate to True and print "0.1234568"
# Or if you want to use the current precision:
#     if FloatHandler.eq(0, 0.00000000000001):
#         print("equal")
FloatHandler = StdFloatHandler()  # pylint: disable=C0103


# Considered using the standard Python decimal for this, but it seems that decimals are lost:
# decimal.getcontext().prec = 7
#     a = decimal.Decimal(1) / decimal.Decimal(3)
#     a
#     -> Decimal('0.3333333')
#     decimal.getcontext().prec = 10
#     a
#     -> Decimal('0.3333333')
#     float(a)
#     -> 0.3333333
# That isn't what I want. I want to keep all decimals, but the number should be represented with the
# amount of precision specified (and also compared as if..)
# Besides that:
#     decimal.getcontext().prec = 7
#     decimal.Decimal(1/3)
#     --> Decimal('0.333333333333333314829616256247390992939472198486328125')
# This would mean I have to update alld code to use decimals everywhere. I would like to be able to
# use normal floats, but treat them as with a certain amount of decimals being significant.

class RoundedFloat(float):
    """Use this class for floats to simplify the notation from FloatHandler

    This will keep all decimals for a floating point number, but only represent it as if a certain
    amount of decimals are significant.

    Example usage:
        a = RoundedFloat(0.12345678)
        b = RoundedFloat(0.12345679)
        with FloatHandler(precision=7):
            a == b
            print(a)
    Which will evaluate to True and print "0.1234568"
    """
    def __eq__(self, f):
        """Check wether self == f within a margin."""
        return FloatHandler().eq(self, f)

    def __ne__(self, f):
        """Check wether self != f within a margin."""
        return not FloatHandler().eq(self, f)

    def __lt__(self, f):
        """Check wether self < f within a margin."""
        return FloatHandler().lt(self, f)

    def __le__(self, f):
        """Check wether self <= f within a margin."""
        return FloatHandler().le(self, f)

    def __gt__(self, f):
        """Check wether self > f within a margin."""
        return FloatHandler().gt(self, f)

    def __ge__(self, f):
        """Check wether self >= f within a margin."""
        return FloatHandler().ge(self, f)

    def __add__(self, f):
        """Make sure to keep type if possible."""
        result = float(self) + f
        if isinstance(result, float):
            return self.__class__(result)
        return result

    def __truediv__(self, f):
        """Make sure to keep type if possible."""
        result = float(self) / f
        if isinstance(result, float):
            return self.__class__(result)
        return result

    def __mul__(self, f):
        """Make sure to keep type if possible."""
        result = float(self) * f
        if isinstance(result, float):
            return self.__class__(result)
        return result

    def __neg__(self):
        """Make sure to keep type."""
        return self.__class__(super().__neg__())

    def __pos__(self):
        """Make sure to keep type."""
        return self.__class__(super().__pos__())

    def __pow__(self, f):
        """Make sure to keep type if possible."""
        result = float(self) ** f
        if isinstance(result, float):
            return self.__class__(result)
        return result

    def __sub__(self, f):
        """Make sure to keep type if possible."""
        result = float(self) - f
        if isinstance(result, float):
            return self.__class__(result)
        return result

    def __rtruediv__(self, f):
        """Make sure to keep type if possible."""
        result = f / float(self)
        if isinstance(result, float):
            return self.__class__(result)
        return result

    def __rsub__(self, f):
        """Make sure to keep type if possible."""
        result = f - float(self)
        if isinstance(result, float):
            return self.__class__(result)
        return result

    def __repr__(self):
        """String representation (also used for __str__)."""
        return FloatHandler().to_str(self)

    __radd__ = __add__
    __rmul__ = __mul__

# To save the floats in JSON as I want (ref https://stackoverflow.com/questions/54370322)
json.encoder.c_make_encoder = None
json.encoder.float = RoundedFloat

def _get_mat_rot(w, x, y, z, sign=1):
    """Return matrix for a quarternion that is supposed to represent a rotation

    The function won't check that the quarternion really represents a rotation.
    """
    dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
    dxw, dyw, dzw = 2*x*w, 2*y*w, 2*z*w
    dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
    return Mat([
        Vec([sign*(1-dy2-dz2), sign*(dxy-dzw), sign*(dxz+dyw)]),
        Vec([sign*(dxy+dzw), sign*(1-dx2-dz2), sign*(dyz-dxw)]),
        Vec([sign*(dxz-dyw), sign*(dyz+dxw), sign*(1-dx2-dy2)])])


class NoRotation(Exception):
    """The transform doesn't represent a rotation"""


class UnsupportedTransform(Exception):
    """This isn't a transform or it isn't supported."""


class UnsupportedOperand(Exception):
    """One of the operand aren't supported for this operation"""


# Use tuples instead of lists to enable building sets used for isometries
class Vec(tuple, base.Orbitit):
    """Define a Euclidean vector"""
    is_homogeneous = False

    def __new__(cls, v):
        return tuple.__new__(cls, [float(a) for a in v])

    def __repr__(self):
        s = f"{self.__class__.__name__}({str(self)})"
        if __name__ != '__main__':
            s = f"{__name__}.{s}"
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        return {
            'class': base.class_to_json[self.__class__],
            'data': list(self),
        }

    @classmethod
    def from_dict_data(cls, data):
        """Create object from dictionary data."""
        return cls(data)

    def __str__(self):
        try:
            elements = ", ".join([f2s(i, FloatHandler.precision) for i in self])
        except IndexError:
            elements = ""
        return f"[{elements}]"

    def __add__(self, w):
        return self.__class__([a + b for a, b in zip(self, w)])

    def __radd__(self, w):
        # provide __radd__ for [..] + Vec([..])
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
            try:
                r = r and FloatHandler.eq(a, b)
            except TypeError:
                return False
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
        raise UnsupportedOperand(f"Right-hand operand of type {type(w)} isn't supported with Vec")

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
        raise UnsupportedOperand(f"Right-hand operand of type {type(w)} isn't supported with Vec")

    def __truediv__(self, w):
        if isinstance(w, (int, float)):
            if w == 0:
                w = 1
            return self.__class__([a/w for a in self])
        raise UnsupportedOperand(f"Right-hand operand of type {type(w)} isn't supported with Vec")

    def insert(self, x, i=0):
        """Return new copy with x inserted on position with index i"""
        res = [self[n] for n in range(i)]
        res.append(x)
        res.extend([self[n] for n in range(i, len(self))])
        return Vec(res)

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
        s_norm = self.norm()
        w_norm = w.norm()
        if s_norm == 0 or w_norm == 0:
            raise ValueError("Cannot take angle with nul vector")
        return math.acos((self / s_norm) * (w / w_norm))

    @property
    def homogeneous(self):
        """Return the homogeneous coordinate."""
        result = self.insert(1, i=len(self))
        result.is_homogeneous = True
        return result

    @property
    def cartesian(self):
        """For a homogeneous vector return the coordinate."""
        if FloatHandler.eq(self[-1], 1):
            return Vec([self[i] for i in range(len(self) - 1)])
        if FloatHandler.ne(self[-1], 0):
            return Vec([self[i] / self[-1]  for i in range(len(self) - 1)])
        return Vec([self[i] for i in range(len(self) - 1)])

    # TODO cross product from GA?


class Vec3(Vec):
    """Define a Euclidean vector in 3D"""
    def __new__(cls, v):
        return super().__new__(cls, [float(v[i]) for i in range(3)])

    def cross(self, w):
        "Return the cross product of this vector with 'w'"""
        return self.__class__([
            self[1] * w[2] - self[2] * w[1],
            self[2] * w[0] - self[0] * w[2],
            self[0] * w[1] - self[1] * w[0]])

    def directed_angle(self, v1, vn, ge_0=True):
        """Directed angle from self and v1 when rotating around the axis vn

        With directed is meant that the resulting angle will not just be the smallest angle between
        the two vectors, but the angle is always taken in one direction.

        Make sure self, v1, and vn are geomtypes.Vec3 that are normalised.

        v1: Vec3 object to take angle with. Must be normalised.
        vn: must be the normalised axis orthogonal to self and v1.
        ge_0: set to False if you require the domain to be (-pi, pi] which will also save an extra
            step in the code. Leaving this to the default value (True) will result in an angle of
            domain [0, 2pi)

        Return: angle in radians
        """
        angle = math.atan2(self.cross(v1) * vn, self * v1)
        if ge_0:
            angle = angle % (2 * math.pi)
        return angle

    def rotate_at(self, rot, axis_point):
        """Rotate self around an axis that goes through the axis_point.

        rot: the rotation of type Rot3
        axis_point: a point on the rotation axis

        Return: a new point
        """
        result = self - axis_point
        result = rot * result
        result += axis_point
        return result

    # TODO implement Scenes3D.getAxis2AxisRotation here


UX = Vec3([1, 0, 0])
UY = Vec3([0, 1, 0])
UZ = Vec3([0, 0, 1])


class Vec4(Vec):
    """Define a Euclidean vector in 4D"""
    def __new__(cls, v):
        """Create a new object."""
        return super().__new__(cls, [float(v[i]) for i in range(4)])

    def is_parallel(self, v):
        """Return whether 'v' is parallel to this vector"""
        z0 = z1 = z2 = z3 = False  # expresses whether self[i] == v[i] == 0
        q0, q1, q2, q3 = 1, 2, 3, 4  # initialise all differently
        try:
            q0 = self[0]/v[0]
        except ZeroDivisionError:
            z0 = FloatHandler.eq(self[0], 0.0)
        try:
            q1 = self[1]/v[1]
        except ZeroDivisionError:
            z1 = FloatHandler.eq(self[1], 0.0)
        try:
            q2 = self[2]/v[2]
        except ZeroDivisionError:
            z2 = FloatHandler.eq(self[2], 0.0)
        try:
            q3 = self[3]/v[3]
        except ZeroDivisionError:
            z3 = FloatHandler.eq(self[3], 0.0)
        if not z0:
            return (z1 or FloatHandler.eq(q0, q1)) and \
                    (z2 or FloatHandler.eq(q0, q2)) and \
                    (z3 or FloatHandler.eq(q0, q3))
        if not z1:
            return (z0 or FloatHandler.eq(q1, q0)) and \
                (z2 or FloatHandler.eq(q1, q2)) and \
                (z3 or FloatHandler.eq(q1, q3))
        if not z2:
            return (z0 or FloatHandler.eq(q2, q0)) and \
                (z1 or FloatHandler.eq(q2, q1)) and \
                (z3 or FloatHandler.eq(q2, q3))
        if not z3:
            return (z0 or FloatHandler.eq(q3, q0)) and \
                (z1 or FloatHandler.eq(q3, q1)) and \
                (z2 or FloatHandler.eq(q3, q2))
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
            repr(w) + '; v = ' + repr(v)
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
        return super().__new__(cls, [float(v[i]) for i in range(4)])

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called,unused-argument
        self._cache = {}

    @classmethod
    def from_dict_data(cls, data):
        """Create object from dictionary data."""
        result = super().from_dict_data(data)
        assert len(result) == 4, f"Expected 4 input values, not {len(result)}"
        return result

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
        raise UnsupportedOperand(f"Right-hand operand of type {type(w)} isn't supported with Quat")

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


class Transform3(tuple, base.Orbitit):
    """Define a 3D tranformation using quarternions"""
    debug = False

    def __new__(cls, quat_pair):
        """Create a new Transform object.

        quat_pair: a pair of quaternions representing the transform
        """
        assert_str = "A 3D transform is represented by 2 quaternions: "
        assert len(quat_pair) == 2, assert_str + str(quat_pair)
        assert isinstance(quat_pair[0], Quat), assert_str + str(quat_pair)
        assert isinstance(quat_pair[1], Quat), assert_str + str(quat_pair)
        return super().__new__(cls, quat_pair)

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called,unused-argument
        self._cache = {}

    def __repr__(self):
        s = indent.Str(f"{_transform3_type_str(self.type())}((\n")
        s = s.add_incr_line(f"{repr(Quat(self[0]))},")
        s = s.add_line(f"{repr(Quat(self[1]))},")
        s = s.add_decr_line('))')
        if __name__ != '__main__':
            s = s.insert(f"{__name__}.")
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        return {
            'class': base.class_to_json[self.__class__],
            'data': [self[0].repr_dict, self[1].repr_dict],
        }

    @classmethod
    def from_dict_data(cls, data):
        """Create object from dictionary data."""
        assert len(data) == 2, f"Expected a pair, not {len(data)} elements"
        return cls([Quat.from_json_dict(q) for q in data])

    def __hash__(self):
        if 'hash_nr' not in self._cache:
            if self.is_rot():
                self._cache['hash_nr'] = self.__hash_rot()
            elif self.is_refl():
                self._cache['hash_nr'] = self.__hash_refl()
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
        return f"{self[0]} * .. * {self[1]}"

    def __mul__(self, u):
        if isinstance(u, Transform3):
            # self * u =  wLeft * vLeft .. vRight * wRight
            return Transform3([self[0] * u[0], u[1] * self[1]])
        # TODO: check kind of Transform3 and optimise
        if isinstance(u, Vec) and len(u) == 3:
            return (self[0] * Quat([0, u[0], u[1], u[2]]) * self[1]).V()
        if isinstance(u, Quat):
            return (self[0] * u * self[1]).V()
        if isinstance(u, Rot3NonCentered):
            return self.matrix(homogeneous=True) * u.matrix()
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
                logging.info(
                    "fallback: %s == %s and %s == %s",
                    self[0],
                    u[0],
                    self[1],
                    u[1],
                )
            assert not is_eq, \
                f"oops, fallback: unknown transform \n{self}\nor\n{u}"
            return is_eq
        if (is_eq and (self.__hash__() != u.__hash__())):
            logging.info(
                "Note: transforms considered equal, but hashes will not be for\n%s and\n%s",
                self,
                u,
            )
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
        raise UnsupportedTransform(f"Not a (supported) transform: {self[1].norm()} != 1?")

    # TODO make this a property e.a.
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
            f"oops, unknown angle; transform {self} neither a rotation, nor a rotary-inversion "
            "(-reflection)"
        )

    # TODO make this a property e.a.
    def axis(self):
        """In case this transform contains a rotation, return the axis

        Otherwise raise a NoRotation exception
        """
        if self.is_rot():
            return self.__axis_rot()
        if self.is_rot_inv():
            return self.__axis_rot_inv()
        raise NoRotation(
            f"oops, unknown axis; transform {self} is neither a rotation, nor a rotary-inversion "
            "(-reflection)"
        )

    def glMatrix(self):
        """Return the glMatrix representation of this transform"""
        return self.matrix(homogeneous=True).transpose()

    def matrix(self, homogeneous=False):
        """Return the matrix representation of this transform.

        homogeneous: set to True to get a 4x4 representation.
        """
        if self.is_rot():
            result = self.__matrix_rot()
        elif self.is_refl():
            result = self.__matrix_refl()
        elif self.is_rot_inv():
            result = self.__matrix_rot_inv()
        else:
            raise UnsupportedTransform(f"oops, unknown matrix; transform {self}\n")

        if not homogeneous:
            return result

        return result.homogeneous

    def inverse(self):
        """Return a new object with the inverse of this transform"""
        if self.is_rot():
            return self.__inverse_rot()
        if self.is_refl():
            return self.__inverse_refl()
        if self.is_rot_inv():
            return self.__inverse_rot_inv()
        raise UnsupportedTransform(f"oops, unknown matrix; transform {self}\n")

    def __neg__(self):
        """Return a new object with the inverse of this transform"""
        return self.inverse()

    def is_direct(self):
        """Return whether this is an opposite transform (i.e. not direct)"""
        return self.is_rot()

    def is_opposite(self):
        """Return whether this is an opposite transform (i.e. not direct)"""
        return not self.is_direct()

    # *** ROTATION specific functions:
    def is_rot(self):
        """Return whether this tranform is a rotation."""
        d = 1 - FloatHandler.margin
        with FloatHandler(1 - d * d) as fh:
            eq_square_norm = fh.eq(self[1].squared_norm(), 1)
        return (
            self[1].conjugate() == self[0]
            and
            eq_square_norm
            and
            (self[1].S() < 1 or FloatHandler.eq(self[1].S(), 1))
            and
            (self[1].S() > -1 or FloatHandler.eq(self[1].S(), -1))
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
            (FloatHandler.eq(self[0][0], 0) and self[0] == u[1])
        )

    def __hash_rot(self):
        axis = self.__axis_rot()
        return hash((self.Rot,
                     round(self.__angle_rot(), FLOAT_PRECISION),
                     round(axis[0], FLOAT_PRECISION),
                     round(axis[1], FLOAT_PRECISION),
                     round(axis[2], FLOAT_PRECISION)))

    def __str_rot(self):
        axis = self.__axis_rot()
        return (
            f"Rotation of {f2s(to_degrees(self.__angle_rot()))} "
            "degrees around ["
            f"{f2s(axis[0])}, "
            f"{f2s(axis[1])}, "
            f"{f2s(axis[2])}]"
        )

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
                f"{repr(self)} doesn't represent a rotation"
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
                        f"{repr(self)} doesn't represent a rotation"
                    sin = 0
        self._cache['angleRot'] = 2 * math.atan2(sin, cos)

        # make unique: -pi < angle < pi
        if not (self._cache['angleRot'] < math.pi
                or FloatHandler.eq(self._cache['angleRot'], math.pi)):
            self._cache['angleRot'] = self._cache['angleRot'] - \
                2 * math.pi
        if not (self._cache['angleRot'] > -math.pi
                or FloatHandler.eq(self._cache['angleRot'], -math.pi)):
            self._cache['angleRot'] = self._cache['angleRot'] + \
                2 * math.pi

        # make unique: 0 < angle < pi
        if FloatHandler.eq(self._cache['angleRot'], 0):
            self._cache['angleRot'] = 0.0
        if self._cache['angleRot'] < 0:
            self._cache['angleRot'] = -self._cache['angleRot']
            self._cache['axisRot'] = -self._cache['axisRot']
        if FloatHandler.eq(self._cache['angleRot'], math.pi):
            # if halfturn, make axis unique: make the first non-zero element
            # positive:
            if FloatHandler.eq(self._cache['axisRot'][0], 0):
                self._cache['axisRot'] = Vec3(
                    [0.0,
                     self._cache['axisRot'][1],
                     self._cache['axisRot'][2]])
            if self._cache['axisRot'][0] < 0:
                self._cache['axisRot'] = -self._cache['axisRot']
            elif self._cache['axisRot'][0] == 0:
                if FloatHandler.eq(self._cache['axisRot'][1], 0):
                    self._cache['axisRot'] = Vec3(
                        [0.0, 0.0, self._cache['axisRot'][2]])
                if self._cache['axisRot'][1] < 0:
                    self._cache['axisRot'] = -self._cache['axisRot']
                elif self._cache['axisRot'][1] == 0:
                    # not valid axis: if FloatHandler.eq(self._cache['axisRot'][2], 0):
                    if self._cache['axisRot'][2] < 0:
                        self._cache['axisRot'] = -self._cache['axisRot']
        elif FloatHandler.eq(self._cache['angleRot'], 0):
            self._cache['angleRot'] = 0.0
            self._cache['axisRot'] = Vec3([1.0, 0.0, 0.0])

    def __matrix_rot(self):
        if 'matrix_rot' not in self._cache:
            w, x, y, z = self[0]
            self._cache['matrix_rot'] = _get_mat_rot(w, x, y, z)
        return self._cache['matrix_rot']

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
            FloatHandler.eq(self[1].squared_norm(), 1)
            and
            FloatHandler.eq(self[1].S(), 0)
        )

    def __eq_refl(self, u):
        """Compare two transforms that represent reflections"""
        # not needed: and self[1] == u[1]
        # since __eq_refl is called for self and u reflections
        return (self[0] == u[0]) or (self[0] == -u[0])

    def __hash_refl(self):
        normal = self.plane_normal()
        return hash(
            (
                self.Refl,
                self.Refl,  # to use a tuple of 5 elements for all types
                round(normal[0], FLOAT_PRECISION),
                round(normal[1], FLOAT_PRECISION),
                round(normal[2], FLOAT_PRECISION)
            )
        )

    def __str_refl(self):
        norm = self.plane_normal()
        return (
            "Reflection in plane with normal ["
            f"{f2s(norm[0])}, "
            f"{f2s(norm[1])}, "
            f"{f2s(norm[2])}]"
        )

    def plane_normal(self):
        """If this is a reflection, return the plane normal.

        Should only be called when this is a reflection.
        """
        if 'plane_normal' not in self._cache:
            self._cache['plane_normal'] = self[0].V()
            # make normal unique: make the first non-zero element positive:
            if FloatHandler.eq(self._cache['plane_normal'][0], 0):
                self._cache['plane_normal'] = Vec3(
                    [0.0,
                     self._cache['plane_normal'][1],
                     self._cache['plane_normal'][2]])
            if self._cache['plane_normal'][0] < 0:
                self._cache['plane_normal'] = -self._cache[
                    'plane_normal']
            elif self._cache['plane_normal'][0] == 0:
                if FloatHandler.eq(self._cache['plane_normal'][1], 0):
                    self._cache['plane_normal'] = Vec3(
                        [0.0, 0.0, self._cache['plane_normal'][2]])
                if self._cache['plane_normal'][1] < 0:
                    self._cache['plane_normal'] = -self._cache[
                        'plane_normal']
                elif self._cache['plane_normal'][1] == 0:
                    # not needed (since not valid axis):
                    # if FloatHandler.eq(self._cache['plane_normal'][2], 0):
                    if self._cache['plane_normal'][2] < 0:
                        self._cache['plane_normal'] = -self._cache[
                            'plane_normal']
        return self._cache['plane_normal']

    def __matrix_refl(self):
        if 'matrix_refl' not in self._cache:
            _, x, y, z = self[0]
            dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
            dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
            self._cache['matrix_refl'] = Mat([
                Vec([1-dx2, -dxy, -dxz]),
                Vec([-dxy, 1-dy2, -dyz]),
                Vec([-dxz, -dyz, 1-dz2]),
            ])
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
                     round(self.__angle_rot_inv(), FLOAT_PRECISION),
                     round(axis[0], FLOAT_PRECISION),
                     round(axis[1], FLOAT_PRECISION),
                     round(axis[2], FLOAT_PRECISION)))

    def __str_rot_inv(self):
        r = self.I()
        axis = r.axis()
        return (
            f"Rotary inversion of {f2s(to_degrees(r.angle()))} "
            "degrees around ["
            f"{f2s(axis[0])}, "
            f"{f2s(axis[1])}, "
            f"{f2s(axis[2])}]"
        )

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
        Initialise a 3D rotation.

        quat_pair: a pair of quaternions representing the transform
        axis: axis to rotate around: doesn't need to be normalised
        angle: angle in radians to rotate
        """
        if _is_quat_pair(quat):
            trans = super().__new__(cls, quat)
            if not trans.is_rot():
                raise NoRotation(f"{quat} doesn't represent a rotation")
            return trans

        if isinstance(quat, Quat):
            try:
                quat = quat.normalise()
            except ZeroDivisionError:
                pass  # raise exception below
            trans = super().__new__(cls, (quat, quat.conjugate()))
            if not trans.is_rot():
                raise NoRotation(f"{quat} doesn't represent a rotation")
            return trans

        # quat = cos(angle) + y sin(angle)
        alpha = angle / 2
        # if axis is specified as e.g. a list:
        if not isinstance(axis, Vec):
            axis = Vec3(axis)
        if axis != Vec3([0, 0, 0]):
            axis = axis.normalise()
        quat = math.sin(alpha) * axis
        quat = Quat([math.cos(alpha), quat[0], quat[1], quat[2]])
        return super().__new__(cls, (quat, quat.conjugate()))


class HalfTurn3(Rot3):
    """Define a half-turn (rotation)

    quat_pair: ignored argument added to be compatible with Rot3
    axis: named argument holding the axis to rotate around
    angle: ignored argument added to be compatible with Rot3
    """
    def __new__(cls, quat_pair=None, axis=None, angle=0):
        del quat_pair, angle
        assert axis is not None, "You must specify an axis"
        return Rot3.__new__(cls, axis=axis, angle=HALF_TURN)


class Rotx(Rot3):
    """Define a rotation around the x-axis

    quat_pair: ignored argument added to be compatible with Rot3
    axis: ignored argument added to be compatible with Rot3
    angle: named argument holding the rotation angle in radians
    """
    def __new__(cls, quat_pair=None, axis=None, angle=0):
        del quat_pair, axis
        return Rot3.__new__(cls, axis=UX, angle=angle)


class Roty(Rot3):
    """Define a rotation around the y-axis

    quat_pair: ignored argument added to be compatible with Rot3
    axis: ignored argument added to be compatible with Rot3
    angle: named argument holding the rotation angle in radians
    """
    def __new__(cls, quat_pair=None, axis=None, angle=0):
        del quat_pair, axis
        return Rot3.__new__(cls, axis=UY, angle=angle)


class Rotz(Rot3):
    """Define a rotation around the z-axis

    quat_pair: ignored argument added to be compatible with Rot3
    axis: ignored argument added to be compatible with Rot3
    angle: named argument holding the rotation angle in radians
    """
    def __new__(cls, quat_pair=None, axis=None, angle=0):
        del quat_pair, axis
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
            result = super().__new__(cls, quat)
            assert result.is_refl(), f"{quat} doesn't represent a reflection"
        elif isinstance(quat, Quat):
            try:
                quat = quat.normalise()
            except ZeroDivisionError:
                pass  # will fail on assert below:
            result = super().__new__(cls, (quat, quat))
            assert result.is_refl(), f"{quat} doesn't represent a reflection"
        else:
            try:
                normal = normal.normalise()
                quat = Quat(normal)
            except ZeroDivisionError:
                quat = Quat(normal)  # will fail on assert below:
            result = super().__new__(cls, (quat, quat))
            assert result.is_refl(), \
                f"normal {normal} doesn't define a valid 3D plane normal"
        return result


class RotInv3(Transform3):
    """Define a rotary inversion"""
    def __new__(cls, quat_pair=None, axis=None, angle=None):
        """
        Initialise a 3D rotation

        quat_pair: a pair of quaternions representing the transform
        axis: axis to rotate around: doesn't need to be normalised
        angle: angle in radians to rotate
        """
        # Do not inherit from Rot3 (and then apply inversion):
        # a rotary inversion is not a rotation.
        result = None
        if _is_quat_pair(quat_pair):
            result = super().__new__(cls, quat_pair)
            result._cache = {}
            assert result.is_rot_inv(), f"{quat_pair} doesn't represent a rotary inversion"
        else:
            ri = Rot3(quat_pair, axis, angle).I()
            result = super().__new__(cls, (ri[0], ri[1]))
        return result


RotRefl = RotInv3
HX = HalfTurn3(axis=UX)
HY = HalfTurn3(axis=UY)
HZ = HalfTurn3(axis=UZ)
I = RotInv3(Quat([1, 0, 0, 0]))
E = Rot3(Quat([1, 0, 0, 0]))


class Rot3NonCentered():
    """A 3D rotation around an axis that doesn't intersect the origin."""
    def __init__(self, axis, axis_point, angle):
        """
        Initialise the 3D rotation.

        axis: axis to rotate around: doesn't need to be normalised
        axis_point: a point on the axis
        angle: angle in radians to rotate
        """
        # the rotation if the origin was on the axis
        self.rot3 = Rot3(axis=axis, angle=angle)
        self.axis = Vec3(axis)
        self.axis_point = Vec3(axis_point)
        self.angle = angle

    def glMatrix(self):
        """Return the glMatrix representation of this transform"""
        return self.matrix().transpose()

    def matrix(self, **_):
        """Return the 4x4 matrix representation of this transform.

        _: ignored. This is added to be compatible with other 3D transforms
        """
        result = self.rot3.matrix(homogeneous=False)

        # What needs to be done:
        # 1. a translation -t that translate the axis_point to the origin
        # 2. the rotation
        # 3. translate back to axis_point, i.e. translate by t
        # The resulting translation in the matrix is the -rotation*t + t
        def rotate_one(i):
            """rotate one translation element."""
            t = 0
            for j in range(3):
                t += -self.axis_point[j] * result[i][j]
            return t + self.axis_point[i]

        translate = [rotate_one(i) for i in range(3)]
        result = result.insert_col(translate, 3)
        result = result.insert_row(Vec([0, 0, 0, 1]), 3)
        result.is_homogeneous = True

        return result

    def is_opposite(self):
        """Return False a rotation is never opposite."""
        return False

    @overload
    def __mul__(self, v: Vec3) -> Vec3:
        """Left rotate a 3D vector and return as 3D vector"""

    @overload
    def __mul__(self, t: Transform3) -> Vec3:
        """Left rotate a transform and return a homogeneous Mat object"""

    @overload
    def __mul__(self, t: Mat) -> Mat:
        """Left rotate a matrix representing a 3D transform."""

    @overload
    def __mul__(self, t: Rot3NonCentered) -> Mat:
        """Left rotate a matrix representing a 3D transform."""

    def __mul__(self, w):
        right_side = w
        return_vec = False
        right_side_vec = False
        if isinstance(right_side, Vec3):
            right_side = right_side.homogeneous
            right_side_vec = True
            return_vec = True
        elif isinstance(right_side, Transform3):
            right_side = right_side.matrix(homogeneous=True)
        elif isinstance(right_side, Rot3NonCentered):
            right_side = right_side.matrix()
        elif isinstance(right_side, Mat):
            if right_side.rows == 3:
                assert right_side.cols == 3
                right_side = right_side.homogeneous
        else:
            raise NotImplementedError

        assert len(right_side) == 4
        assert right_side_vec or right_side.cols == 4
        result = self.matrix() * right_side

        if return_vec:
            return result.cartesian
        return result


# TODO: make the 3D case a special case of 4D...
class Transform4(tuple):
    """Define a tranform in 4D"""
    def __new__(cls, quat_pair):
        assert_str = "A 4D transform is represented by 2 quaternions: "
        assert len(quat_pair) == 2, assert_str + str(quat_pair)
        assert isinstance(quat_pair[0], Quat), assert_str + str(quat_pair)
        assert isinstance(quat_pair[1], Quat), assert_str + str(quat_pair)
        return tuple.__new__(cls, quat_pair)

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
            f'oops, unknown angle; transform {repr(self)} is '
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )

    def is_rot(self):
        """Whether self represents a rotation"""
        return (
            FloatHandler.eq(self[0].squared_norm(), 1)
            and FloatHandler.eq(self[1].squared_norm(), 1)
        )

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
                        f"{repr(self)} doesn't represent a rotation"
                    return 0
        return 2 * math.atan2(sin, cos)


class Rot4(Transform4):
    """Define a rotation in 4D"""
    def __new__(cls,
                quat_pair=None,
                axialPlane=(Vec4([0, 0, 1, 0]), Vec4([0, 0, 0, 1])),
                angle=0):
        """
        Initialise a 4D rotation
        """
        assert_str = "A 4D rotation is represented by 2 orthogonal axis: "
        assert len(axialPlane) == 2, assert_str + str(axialPlane)
        assert FloatHandler.eq(axialPlane[0] * axialPlane[1], 0), assert_str + str(axialPlane)
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
        assert FloatHandler.eq(_q0.scalar(), 0), assert_str + str(_q0.scalar())
        assert FloatHandler.eq(_q1.scalar(), 0), assert_str + str(_q1.scalar())
        alpha = angle / 2
        sina = math.sin(alpha)
        cosa = math.cos(alpha)
        _q0 = sina * _q0.vector()
        _q1 = sina * _q1.vector()
        return super().__new__(
            cls,
            (
                Quat([cosa, _q0[0], _q0[1], _q0[2]]),
                Quat([cosa, _q1[0], _q1[1], _q1[2]]),
            ),
        )


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
            if FloatHandler.eq(v[i], 0):
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
                quat_pair=None,
                axialPlane=(Vec4([0, 0, 1, 0]), Vec4([0, 0, 0, 1])),
                angle=(0, 0)):
        ortho_plane = find_orthogonal_plane(axialPlane)
        r0 = Rot4(axialPlane=axialPlane, angle=angle[0])
        r1 = Rot4(axialPlane=ortho_plane, angle=angle[1])
        return super().__new__(cls, (r1[0]*r0[0], r0[1]*r1[1]))

# TODO implement geom_3d.Line3D here (in this file)

# forced to use some matrix functions and don't want to add a dependency on a
# big python package.


class Mat(list):
    """Contruct matrix"""
    is_homogeneous = False

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
        s = '['
        c = '\n'
        for row in self:
            s += f'{c}  {row}'
            c = ',\n'
        s += '\n]'
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

    def insert_row(self, row, i=0):
        """Return copy with inserted row at position with index i"""
        result = self[:]
        result.insert(i, Vec(row))
        return self.__class__(result)

    def insert_col(self, col, i=0):
        """Return copy with a column inserted at position with index i"""
        return self.__class__([
            Vec(tuple(row[0:i]) + tuple([x]) + tuple(row[i:]))
            for row, x in zip(self, col)])

    def rm_row(self, i):
        """Return copy with deleted row i"""
        # don't use self.pop(i), it changes self, while the result should be
        # returned instead.
        if i < 0:
            i += self.rows
        assert i >= 0
        n = self[0:i]
        n.extend(self[i+1:])
        return Mat(n)

    def rm_col(self, i):
        """Return copy with deleted column i"""
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
        for k, row in zip(list(range(self.rows)), self):
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
            if not FloatHandler.eq(self[0][i], 0):
                r += sign * self[0][i] * self.minor(0, i)
            sign = -sign
        return r

    @property
    def determinant(self):
        """Determinant of matrix"""
        return self.det()

    def is_opposite(self):
        """Return whether this matrix represents an opposite transform."""
        return self.determinant < 0

    def __mul__(self, n):
        """Mulitply matrix with matrix / vector"""
        result = None
        if isinstance(n, Mat):
            assert self.rows == n.cols
            assert n.rows == self.cols
            n_t = n.T()
            result = Mat([Vec([row * col for col in n_t]) for row in self])
            result.is_homogeneous = self.is_homogeneous
        elif isinstance(n, Vec):
            left_side = self
            right_side = n
            if left_side.rows == len(right_side) + 1:
                right_side = right_side.homogeneous
            if left_side.rows + 1 == len(right_side) and not left_side.is_homogeneous:
                left_side = left_side.homogeneous
            assert left_side.rows == len(right_side)
            result = Vec([row * right_side for row in left_side])
            if right_side.is_homogeneous and not n.is_homogeneous:
                result = result.cartesian
        elif isinstance(n, Rot3NonCentered):
            right_side = n.matrix()
            left_side = self
            if left_side.rows == right_side.rows + 1:
                right_side = right_side.homogeneous
            elif left_side.rows + 1 == right_side.rows:
                left_side = left_side.homogeneous
            assert left_side.rows == right_side.rows
            assert left_side.cols == right_side.cols
            result = left_side * right_side
        else:
            assert False, f'unknown type of object to multiply matrix: {n}.'
        return result

    def inverse(self):
        """Return inverse matrix"""
        if self.orthogonal():
            return self.T()

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
        if det == 0:
            raise ValueError(f"No solution for {self}")
        return Vec(
            [self.replace_col(i, v).det() / det for i in range(self.cols)])

    @property
    def homogeneous(self):
        """Return the homogeneous coordinate."""
        if self.is_homogeneous:
            return self

        last = len(self)
        result = self.insert_col([0 if i != last - 1 else 1 for i in range(last)], last)
        result = result.insert_row([0 if i != last else 1 for i in range(last + 1)], last)
        result.is_homogeneous = True
        return result

    def glMatrix(self):
        """Return the glMatrix representation"""
        return self.homogeneous.transpose()


class Line:
    """A base class for representing a line in any dimension.

    Attributes:
        - p: base point of the line, it is point on the line.
        - v: direction vector of the line.
        - dimension: the spade dimension the line is defined in
        - is_segment: if False the line is infinite, otherwise this is a finite line only valid for
            the values p + t.v with t in [0, 1]
    """

    def __init__(self, p0, p1=None, v=None, d=None, is_segment=False):
        """
        Define a line in a d dimensional space.

        Either specify two distinctive points p0 and p1 on the d dimensional
        line or specify a base point p0 and directional vector v. Points p0 and
        p1 should have accessable [0] .. [d-1] indices.
        """
        assert (
            p1 is None or v is None
        ), "Specify either 2 points p0 and p1 or a base point p0 and a direction v!"
        self.is_segment = is_segment
        if d:
            self.dimension = d
            assert len(p0) >= d
        else:
            self.dimension = len(p0)
        p0 = self._chk_point(p0)
        if p1 is not None:
            self._set_points(p0, self._chk_point(p1))
        elif v is not None:
            self._define_line(p0, self._chk_point(v))

    def _chk_point(self, v):
        """Check dimension and ensure vector type."""
        assert len(v) == self.dimension, (
            f"Wrong dimension vector, got {v}, expected {self.dimension}"
        )
        # if len(v) > self.dimension:
        #     v = v[:self.dimension]
        if not isinstance(v, Vec):
            v = Vec(v)
        return v

    def _set_points(self, p0, p1):
        """From two points 'p0' and 'p1' define the line."""
        self._define_line(p0, p1 - p0)

    def _define_line(self, p, v):
        """From a point 'p' and a direction vector 'v' define the line."""
        self.p = p
        self.v = v
        self.p1 = self.get_point(1)

    @property
    def p0(self):
        """Return base point of the line."""
        return self.p

    def get_point(self, t):
        """Return the point on the line that equals to self.b + t*self.v (or [] when t is None)

        t: the slope factor, For 0 the starting point p0 from ___init is returned, for 1 the end
            point p1 is returned.

        return: the point is an instance of Vec. This will return a point even for segments where
        you fill in a value of t that isn't part of the domain [0, 1]
        """
        if t is not None:
            return Vec([self.p[i] + t * (self.v[i]) for i in range(self.dimension)])
        return Vec([])

    def get_factor_at(self, c, i):
        """
        For an n-dimensional line l = p + t.v it get the factor t for which p[i] + t.v[i] = c

        c: the constant
        i: index of element that should equal to c

        return: a RoundedFloat number or None if:
           1. the line lies in the (n-1) (hyper)plane x_i == c
           2. or the line never intersects the (n-1) (hyper)plane x_i == c.
        """
        if not FloatHandler.eq(self.v[i], 0.0):
            return RoundedFloat((c - self.p[i]) / self.v[i])
        return None

    def is_valid_factor(self, t):
        """Return a boolean expresssing whether the factor value 't'  is valid."""
        if self.is_segment:
            return 0 <= t <= 1
        return True

    def is_on_line(self, v):
        """
        Return True if vertex 'v' is on the line, False otherwise

        If the line is a segment then False is returned when the point is on the line, but outside
        the segment.

        v: a point which should be an instance of Vec with the same dimension of the line.
        """
        t = None
        for i, v_i in enumerate(v):
            t = self.get_factor_at(v_i, i)
            if t is not None:
                break
            # else either 0 or an infinite amount of solutions (e.g. line x == 1 while looking for
            # specific x coordinate)

        if self.is_valid_factor(t):
            return self.get_point(t) == v
        return False

    def get_factor(self, p, check=True):
        """Assuming the point p lies on the line, the factor is returned.

        If the line is a segment. i.e. if the line isn't infinite a ValueError is raised if it
        isn't on the segment.

        p: a point which should be an instance of geomtypes.Vec
        check: if set, then the method will check whether the point is on the line using the current
        precision of geomtypes.FloatHandler. If not a ValueError is raised.

        """
        for i in range(self.dimension):
            t = self.get_factor_at(p[i], i)
            if t is not None:
                break
        assert t is not None
        if check:
            c = self.get_point(t)
            if not c == p[:self.dimension]:
                logging.warning(
                    "The point is not on the line; yDiff = %f", c[i] - p[i]
                )
                raise ValueError("The point is not on the line according to the current precision")
        if self.is_segment:
            if not 0 <= t <= 1:
                logging.warning("The point is not on the line segment; t = %f not in [0, 1]", t)
                raise ValueError("The point is not on the line segment (with current precisio)")
        return RoundedFloat(t)

    def __repr__(self):
        """Get a string representation of the line."""
        return f"{self.p} + t.{self.v}"


# Classes that support conversion from and to JSON:
base.class_to_json[Vec] = "vector"
base.class_to_json[Vec3] = "vector_3"
base.class_to_json[Vec4] = "vector_4"
base.class_to_json[Quat] = "quaternion"
base.json_to_class["vector"] = Vec
base.json_to_class["vector_3"] = Vec3
base.json_to_class["vector_4"] = Vec4
base.json_to_class["quaternion"] = Quat

# All Transform3 derivatives are saved as Transform3, since they only have a different __new__ and
# not all support quat_pair.
base.class_to_json[Transform3] = "transform_3d"
base.class_to_json[Rot3] = "transform_3d"
base.class_to_json[Refl3] = "transform_3d"
base.class_to_json[RotInv3] = "transform_3d"
base.class_to_json[HalfTurn3] = "transform_3d"
base.class_to_json[Rotx] = "transform_3d"
base.class_to_json[Roty] = "transform_3d"
base.class_to_json[Rotz] = "transform_3d"
base.json_to_class["transform_3d"] = Transform3
