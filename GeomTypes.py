#! /usr/bin/python

import math

turn      = lambda r: r * 2 * math.pi
degrees   = lambda r: math.pi * r / 180
toDegrees = lambda r: 180.0 * r   / math.pi

fullTurn = turn(1)
hTurn    = turn(0.5)
qTurn    = turn(0.25)
tTurn    = turn(1.0/3)

eqFloatMargin = 1.0e-15
def eq(a, b):
    """
    Check if 2 floats 'a' and 'b' are close enough to be called equal.

    a: a floating point number.
    b: a floating point number.
    margin: if |a - b| < margin then the floats will be considered equal and
            True is returned.
    """
    return abs(a - b) < eqFloatMargin

# Use tuples instead of lists to enable building sets used for isometries

class Vec(tuple):
    def __new__(this, v):
        return tuple.__new__(this, [float(a) for a in v])

    def __repr__(v):
        return '%s(%s)' % (v.__class__.__name__, str(v))

    def __str__(v):
        try:
            s = '[%s' % v[0]
            for i in range(1, len(v)): s = '%s, %s' % (s, v[i])
            return '%s]' % s
        except IndexError:
            return '[]'

    def __add__(v, w):
        return v.__class__([a+b for a, b in zip(v, w)])

    def __radd__(v, w):
        # provide __radd__ for [..] + Vec([..])
        print 'v', v, 'w', w
        return v.__class__([a+b for a, b in zip(v, w)])

    def __sub__(v, w):
        return v.__class__([a-b for a, b in zip(v, w)])

    def __rsub__(v, w):
        # provide __rsub__ for [..] + Vec([..])
        return v.__class__([b-a for a, b in zip(v, w)])

    def __eq__(v, w):
        #print '%s ?= %s' % (v, w)
        try:
            r = len(v) == len(w)
        except TypeError:
            #print 'info: comparing different types in Vec (%s and %s)' % (
            #        v.__class__.__name__, w.__class__.__name__
            #    )
            return False
        for a, b in zip(v, w):
            if not r: break
            r = r and eq(a, b)
            #print '%s ?= %s : %s (d = %s)' % (a, b, eq(a, b), a-b)
        return r

    def __ne__(v, w):
        return not(v == w)

    def __neg__(v):
        return v.__class__([-a for a in v])

    def __mul__(v, w):
        if isinstance(w, tuple):
            # dot product
            r = 0
            for a, b in zip(v, w): r += a*b
            return r
        elif isinstance(w, int) or isinstance(w, float):
            return v.__class__([w*a for a in v])

    def __rmul__(v, w):
        if isinstance(w, tuple):
            # provide __rmul__ for [..] + Vec([..])
            # dot product
            r = 0
            for a, b in zip(v, w): r += a*b
            return r
        if isinstance(w, int) or isinstance(w, float):
            return v.__class__([w*a for a in v])

    def __div__(v, w):
        if isinstance(w, int) or isinstance(w, float):
            return v.__class__([a/w for a in v])

    def squareNorm(v):
        r = 0
        for a in v: r += a*a
        return r

    def norm(v):
        return math.sqrt(v.squareNorm())

    def normalise(v):
        return v/v.norm()

    normalize = normalise

    def angle(v, w):
        return math.acos(v.normalise()*w.normalise())

    # TODO cross product from GA?

class Vec3(Vec):
    def __new__(this, v):
        return Vec.__new__(this, [float(v[i]) for i in range(3)])

    def cross(v, w):
        return v.__class__([
                v[1] * w[2] - v[2] * w[1],
                v[2] * w[0] - v[0] * w[2],
                v[0] * w[1] - v[1] * w[0]
            ])

    # TODO implement Scenes3D.getAxis2AxisRotation here

ux = Vec3([1, 0, 0])
uy = Vec3([0, 1, 0])
uz = Vec3([0, 0, 1])

class Vec4(Vec):
    def __new__(this, v):
        return Vec.__new__(this, [float(v[i]) for i in range(4)])

    def isParallel(u, v):
        z0 = z1 = z2 = z3 = False # expresses whether u[i] == v[i] == 0
        q0, q1, q2, q3 = 1, 2, 3, 4 # initialise all differently
        try:
            q0 = u[0]/v[0]
        except ZeroDivisionError:
            z0 = eq(u[0], 0.0)
        try:
            q1 = u[1]/v[1]
        except ZeroDivisionError:
            z1 = eq(u[1], 0.0)
        try:
            q2 = u[2]/v[2]
        except ZeroDivisionError:
            z2 = eq(u[2], 0.0)
        try:
            q3 = u[3]/v[3]
        except ZeroDivisionError:
            z3 = eq(u[3], 0.0)
        if (not z0):
            return (
                    (z1 or eq(q0, q1))
                    and
                    (z2 or eq(q0, q2))
                    and
                    (z3 or eq(q0, q3))
                )
        elif (not z1):
            return (
                    (z0 or eq(q1, q0))
                    and
                    (z2 or eq(q1, q2))
                    and
                    (z3 or eq(q1, q3))
                )
        elif (not z2):
            return (
                    (z0 or eq(q2, q0))
                    and
                    (z1 or eq(q2, q1))
                    and
                    (z3 or eq(q2, q3))
                )
        elif (not z3):
            return (
                    (z0 or eq(q3, q0))
                    and
                    (z1 or eq(q3, q1))
                    and
                    (z2 or eq(q3, q2))
                )
        else:
           # else z0 and z1 and z2 and z3, i.e u == v == (0, 0, 0, 0)
           return True

    def makeOrthogonalTo(w, v):
        """
        Returns the modification of this vector orthogonal to v, while keeping them in the same plane.
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
        assert not w.isParallel(v), 'null vector used or vectors are (too) parallel; this = ' + w.__repr__() + '; v = ' + v.__repr__()
        # TODO: is there a better way to set,...
        return Vec4(p * v + q * w)

    def cross(u, v, w):
        vw_xy = v[0] * w[1] - v[1] * w[0]
        vw_xz = v[0] * w[2] - v[2] * w[0]
        vw_xw = v[0] * w[3] - v[3] * w[0]
        vw_yz = v[1] * w[2] - v[2] * w[1]
        vw_yw = v[1] * w[3] - v[3] * w[1]
        vw_zw = v[2] * w[3] - v[3] * w[2]
        return Vec4([
            u[1]  * vw_zw -  u[2] * vw_yw  +  u[3] * vw_yz,
            -u[0] * vw_zw +  u[2] * vw_xw  -  u[3] * vw_xz,
            u[0]  * vw_yw -  u[1] * vw_xw  +  u[3] * vw_xy,
            -u[0] * vw_yz +  u[1] * vw_xz  -  u[2] * vw_xy
        ])

def unitVec4(i):
    v    = [0, 0, 0, 0]
    v[i] = 1
    return Vec4(v)

class Quat(Vec):
    def __new__(this, v = None):
        # if 3D vector, use it to set vector part only and use 0 for scalar part
        if len(v) == 3: v = [0, v[0], v[1], v[2]]
        return Vec.__new__(this, [float(v[i]) for i in range(4)])

    def conjugate(v):
        return v.__class__([v[0], -v[1], -v[2], -v[3]])

    def __mul__(v, w):
        if isinstance(w, Quat):
            # Quaternion product
            return v.__class__([
                    v[0]*w[0] - v[1]*w[1] - v[2] * w[2] - v[3] * w[3],
                    v[0]*w[1] + v[1]*w[0] + v[2] * w[3] - v[3] * w[2],
                    v[0]*w[2] - v[1]*w[3] + v[2] * w[0] + v[3] * w[1],
                    v[0]*w[3] + v[1]*w[2] - v[2] * w[1] + v[3] * w[0]
                ])
        elif isinstance(w, int) or isinstance(w, float):
            return Vec.__mul__(v, w)

    def dot(v, w):
        return Vec.__mul__(v, w)

    def scalar(v):
        """Returns the scalar part of v"""
        return v[0]

    def vector(v):
        """Returns the vector part of v (as a Vec3)"""
        return Vec3(v[1:])

    inner = dot
    S = scalar
    V = vector

def transform3TypeStr(i):
    if i == Transform3.Rot:    return 'Rot3'
    if i == Transform3.Refl:   return 'Refl3'
    if i == Transform3.RotInv: return 'RotInv3'
    else:                      return 'Transform3'

class Transform3(tuple):
    def __new__(this, quatPair):
        assertStr = "A 3D transform is represented by 2 quaternions: "
        assert len(quatPair) == 2, assertStr + str(quatPair)
        assert isinstance(quatPair[0], Quat), assertStr + str(quatPair)
        assert isinstance(quatPair[1], Quat), assertStr + str(quatPair)
        return tuple.__new__(this, quatPair)

    def __repr__(t):
        return '%s([%s, %s])' % (
                transform3TypeStr(t.type()), str(t[0]), str(t[1])
            )

    def __str__(t):
        if t.isRot(): return t.__strRot()
        elif t.isRefl(): return t.__strRefl()
        elif t.isRotInv(): return t.__strRotInv()
        else:
            return '%s * .. * %s' % (str(t[0]), str(t[1]))

    def __mul__(t, u):
        if isinstance(u, Transform3):
            # t * u =  wLeft * vLeft .. vRight * wRight
            return Transform3([t[0] * u[0], u[1] * t[1]])
        # TODO: check kind of Transform3 and optimise
        elif isinstance(u, Vec) and len(u) == 3:
            return (t[0] * Quat([0, u[0], u[1], u[2]]) * t[1]).V()
        elif isinstance(u, Quat):
            return (t[0] * u                           * t[1]).V()
        else:
            return u.__rmul__(t)
            #raise TypeError, "unsupported op type(s) for *: '%s' and '%s'" % (
            #        t.__class__.__name__, u.__class__.__name__
            #    )

    def __eq__(t, u):
        if not isinstance(u, Transform3): return False
        if t.isRot() and u.isRot: return t.__eqRot(u)
        elif t.isRefl() and u.isRefl: return t.__eqRefl(u)
        elif t.isRotInv() and u.isRotInv: return t.__eqRotInv(u)
        else:
            return (t[0] == u[0] and t[1] == u[1])

    def __ne__(t, u):
        return not(t == u)

    Rot     = 0
    Refl    = 1
    RotInv  = 2
    RotRefl = RotInv
    def type(t):
        if t.isRot(): return t.Rot
        if t.isRefl(): return t.Refl
        if t.isRotInv(): return t.RotInv
        assert False, 'oops, unknown type of Transform: %s ?= 1' % t[1].norm()

    def angle(t):
        if t.isRot(): return t.angleRot()
        if t.isRotInv(): return t.angleRotInv()
        assert False, (
            'oops, unknown angle; transform %s\n' +
            'neither a rotation, nor a rotary-inversion (-reflection)' % t)

    def axis(t):
        if t.isRot(): return t.axisRot()
        if t.isRotInv(): return t.axisRotInv()
        assert False, (
            'oops, unknown angle; transform %s\n' +
            'neither a rotation, nor a rotary-inversion (-reflection)' % t)

    def matrix(t):
        # TODO: test this
        # TODO: add RotInv
        if t.isRot(): return t.matrixRot()
        if t.isRefl(): return t.matrixRefl()
        assert False, (
            'oops, unknown matrix; transform %s\n' +
            'not a rotation' % t)

    def inverse(t):
        if t.isRot(): return t.inverseRot()
        if t.isRefl(): return t.inverseRefl()
        if t.isRotInv(): return t.inverseRotInv()
        assert False, (
            'oops, unknown matrix; transform %s\n' +
            'not a rotation' % t)

    ## ROTATION specific functions:
    def isRot(t):
        #print 't[1].conjugate() == t[0]', t[1].conjugate() == t[0]
        #print '%s = t[1].conjugate() == t[0] %s ' % (
        #        t[1].conjugate(), t[0]
        #    )
        #print '1 ?= t[1].norm() = %0.17f' % t[1].norm()
        #print '-1 ?<= t.S() = %0.17f ?<= 1' % t[1].S()
        return (
            t[1].conjugate() == t[0]
            and
            eq(t[1].squareNorm(), 1)
            and
            (t[1].S() < 1 or eq(t[1].S(), 1))
            and
            (t[1].S() > -1 or eq(t[1].S(), -1))
        )

    def __eqRot(t, u):
        """Compare two transforms that represent rotations
        """
        #print '__eqRot'
        #print '%s ?= %s' % (str(t[0]), str(u[0]))
        #print '%s ?= %s' % (str(t[1]), str(u[1]))
        return (
            (t[0] == u[0] and t[1] == u[1])
            or
            # negative axis with negative angle:
            (t[0] == -u[0] and t[1] == -u[1])
            or
            # half turn (equal angle) around opposite axes
            (eq(t[0][0], 0) and t[0] == u[1])
        )

    def __strRot(t):
        str = 'Rotation of %s rad around %s' % (t.angleRot(), t.axisRot())
        return str

    def angleRot(t):
        cos = t[0][0]
        for i in range(3):
            try:
                sin = t[0][i+1] / t[0].V().normalise()[i]
                break
            except ZeroDivisionError:
                if i == 2:
                    assert ( t[0] == Quat([1, 0, 0, 0]) or
                            t[0] == Quat([-1, 0, 0, 0])
                        ), (
                            "%s doesn't represent a rotation" % t.__repr__()
                        )
                    return 0
        #print 'reconstructed cos =', cos
        #print 'reconstructed sin =', sin
        return 2 * math.atan2(sin, cos)

    def axisRot(t):
        try:
            return t[0].V().normalise()
        except ZeroDivisionError:
            assert (t[0] == Quat([1, 0, 0, 0]) or
                    t[0] == Quat([-1, 0, 0, 0])
                ), (
                    "%s doesn't represent a rotation" % t.__repr__()
                )
            return t[0].V()

    def matrixRot(t):
        w, x, y, z = t[0]
        dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
        dxw, dyw, dzw = 2*x*w, 2*y*w, 2*z*w
        dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
        return [
            Vec([1-dy2-dz2,     dxy-dzw,        dxz+dyw]),
            Vec([dxy+dzw,       1-dx2-dz2,      dyz-dxw]),
            Vec([dxz-dyw,       dyz+dxw,        1-dx2-dy2]),
        ]

    def inverseRot(t):
        return Rot3(axis = t.axis(), angle = -t.angle())

    ## REFLECTION specific functions:
    def isRefl(t):
        #print 't[1] == t[0]:', t[1] == t[0]
        #print '1 ?= t[1].norm() = %0.17f' % t[1].norm()
        #print '0 ?= t[1].S() = %0.17f' % t[1].S()
        return (
            t[1] == t[0]
            and
            eq(t[1].squareNorm(), 1)
            and
            eq(t[1].S(), 0)
        )

    def __eqRefl(t, u):
        """Compare two transforms that represent reflections
        """
        return (
            # not needed: and t[1] == u[1])
            # since __eqRefl is called for t and u reflections
            (t[0] == u[0])
            or
            (t[0] == -u[0])
            # again not needed: and t[1] == u[1])
        )

    def __strRefl(s):
        return 'Reflection in plane with normal %s' % (str(s.planeN()))

    def planeN(s):
        return s[0].V()

    def matrixRefl(t):
        w, x, y, z = t[0]
        dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
        dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
        return [
            Vec([1-dx2,         -dxy,           -dxz]),
            Vec([-dxy,          1-dy2,          -dyz]),
            Vec([-dxz,          -dyz,           1-dz2]),
        ]

    def inverseRefl(t):
        return t

    ## ROTARY INVERSION (= ROTARY RELECTION) specific functions:
    def I(t):
        """
        Apply a central inversion
        """
        return Transform3([-t[0], t[1]])

    def isRotInv(t):
        return t.I().isRot() and not t.isRefl()

    def __eqRotInv(t, u):
        return t.I().isRot() == u.I().isRot()

    def __strRotInv(t):
        r = t.I()
        str = 'Rotary inversion of %s rad around %s' % (
                r.angleRot(), r.axisRot()
            )
        return str

    def angleRotInv(t):
        return t.I().angleRot()

    def axisRotInv(t):
        return t.I().axisRot()

    def inverseRotInv(t):
        return RotInv3(axis = t.axis(), angle = -t.angle())

    isRotRefl   = isRotInv
    axisRotRefl = axisRotInv

    def angleRotRefl(t):
        return (t.angleRotInv() - hTurn)

class Rot3(Transform3):
    def __new__(this, qLeft = None, axis = Vec3([1, 0, 0]), angle = 0):
        """
        Initialise a 3D rotation
        """
        if isinstance(qLeft, Quat):
            try: qLeft = qLeft.normalise()
            except ZeroDivisionError: pass # will fail on assert below:
            t = Transform3.__new__(this, [qLeft, qLeft.conjugate()])
            assert t.isRot(), "%s doesn't represent a rotation" % str(qLeft)
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
            return Transform3.__new__(this, [q, q.conjugate()])

class HalfTurn3(Rot3):
    def __new__(this, axis):
        return Rot3.__new__(this, axis = axis, angle = hTurn)

class Rotx(Rot3):
    def __init__(this, angle):
        return Rot3.__new__(this, axis = ux, angle = angle)

class Roty(Rot3):
    def __new__(this, angle):
        return Rot3.__new__(this, axis = uy, angle = angle)

class Rotz(Rot3):
    def __new__(this, angle):
        return Rot3.__new__(this, axis = uz, angle = angle)

class Refl3(Transform3):
    def __new__(this, q = None, planeN = None):
        """Define a 3D reflection is a plane

        Either define
        q: quaternion representing the left (and right) quaternion
           multiplication for a reflection
        or
        planeN: the 3D normal of the plane in which the reflection takes place.
        """
        if isinstance(q, Quat):
            try: q = q.normalise()
            except ZeroDivisionError: pass # will fail on assert below:
            t = Transform3.__new__(this, [q, q])
            assert t.isRefl(), "%s doesn't represent a reflection" % str(q)
            return t
        else:
            try:
                normal = planeN.normalise()
                q = Quat(normal)
            except ZeroDivisionError:
                q = Quat(planeN) # will fail on assert below:
            t = Transform3.__new__(this, [q, q])
            assert t.isRefl(), (
                "normal %s doesn't define a valid 3D plane normal" % str(planeN)
            )
            return t

class RotInv3(Transform3):
    def __new__(this, qLeft = None, axis = None, angle = None):
        """
        Initialise a 3D rotation
        """
        # Do not inherit from Rot3 (and then apply inversion):
        # a rotary inversion is not a rotation.
        ri = Rot3(qLeft, axis, angle).I()
        return Transform3.__new__(this, [ri[0], ri[1]])

RotRefl = RotInv3
Hx = HalfTurn3(ux)
Hy = HalfTurn3(uy)
Hz = HalfTurn3(uz)
I = RotInv3(Quat([1, 0, 0, 0]))
E = Rot3(Quat([1, 0, 0, 0]))

# TODO: make the 3D case a special case of 4D...
class Transform4(tuple):
    def __new__(this, quatPair):
        assertStr = "A 4D transform is represented by 2 quaternions: "
        assert len(quatPair) == 2, assertStr + str(quatPair)
        assert isinstance(quatPair[0], Quat), assertStr + str(quatPair)
        assert isinstance(quatPair[1], Quat), assertStr + str(quatPair)
        return tuple.__new__(this, quatPair)

    def __mul__(t, u):
        if isinstance(u, Transform4) or isinstance(u, Transform3):
            # t * u =  wLeft * vLeft .. vRight * wRight
            return Transform4([t[0] * u[0], u[1] * t[1]])
        # TODO: check kind of Transform4 and optimise
        elif isinstance(u, Vec) and len(u) == 3:
            return t[0] * Quat([0, u[0], u[1], u[2]]) * t[1]
        elif isinstance(u, Quat):
            return t[0] * u                           * t[1]
        elif isinstance(u, Vec) and len(u) == 4:
            return t[0] * Quat(u)                     * t[1]
        else:
            return u.__rmul__(t)
            #raise TypeError, "unsupported op type(s) for *: '%s' and '%s'" % (
            #        t.__class__.__name__, u.__class__.__name__
            #    )

    def angle(t):
        if t.isRot(): return t.angleRot()
        #if t.isRotInv(): return t.angleRotInv()
        assert False, (
            'oops, unknown angle; transform %s\n' % str(t) +
            'neither a rotation, nor a rotary-inversion (-reflection)'
        )

    #def __repr__(t):
    #    return '%s([%s, %s])' % (
    #            transform3TypeStr(t.type()), str(t[0]), str(t[1])
    #        )

    #def __str__(t):
    #    if t.isRot(): return t.__strRot()
    #    elif t.isRefl(): return t.__strRefl()
    #    elif t.isRotInv(): return t.__strRotInv()
    #    else:
    #        return '%s * .. * %s' % (str(t[0]), str(t[1]))

    def isRot(t):
        # print 't0', t[0].squareNorm() - 1
        # print 't1', t[1].squareNorm() - 1
        return (
            eq(t[0].squareNorm(), 1)
            and
            eq(t[1].squareNorm(), 1)
        )

    def angleRot(t):
        cos = t[0][0]
        for i in range(3):
            try:
                sin = t[0][i+1] / t[0].V().normalise()[i]
                break
            except ZeroDivisionError:
                if i == 2:
                    assert ( t[0] == Quat([1, 0, 0, 0]) or
                            t[0] == Quat([-1, 0, 0, 0])
                        ), (
                            "%s doesn't represent a rotation" % t.__repr__()
                        )
                    return 0
        #print 'reconstructed cos =', cos
        #print 'reconstructed sin =', sin
        return 2 * math.atan2(sin, cos)

class Rot4(Transform4):
    def __new__(this, quatPair = None,
        axialPlane = (Vec4([0, 0, 1, 0]), Vec4([0, 0, 0, 1])),
        angle = 0
    ):
        """
        Initialise a 4D rotation
        """
        if False: pass
        #if isinstance(qLeft, Quat):
        #    try: qLeft = qLeft.normalise()
        #    except ZeroDivisionError: pass # will fail on assert below:
        #    t = Transform3.__new__(this, [qLeft, qLeft.conjugate()])
        #    assert t.isRot(), "%s doesn't represent a rotation" % str(qLeft)
        #    return t
        else:
            assertStr = "A 4D rotation is represented by 2 orthogonal axis: "
            assert len(axialPlane) == 2, assertStr + str(axialPlane)
            assert eq(axialPlane[0] * axialPlane[1], 0
                ), assertStr + str(axialPlane)
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
            return Transform4.__new__(this,
                [
                    Quat([cosa, q0[0], q0[1], q0[2]]),
                    Quat([cosa, q1[0], q1[1], q1[2]])
                ]
            )

def findOrthoPlane(plane):
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
    def getZeroIndex(v, s = 0):
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
    status = { 'sz_e0': -1, 'sz_e1': -1, 'e0_z_e1': 0, 'sp': 0 }

    # define e0 and e1 locally to be able to exchange their roll just for
    # calculating e2 and e3.
    e0 = plane[0].normalise()
    e1 = plane[1].normalise()

    # Now define e2,..
    zi    = getZeroIndex(e0)
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
            vnIni = Vec4(1/e0[0], 1/e0[1], 1/e0[2], 1/e0[3])
            possiblePermuations = [
                Vec4( vnIni[0],  vnIni[1], -vnIni[2], -vnIni[3]),
                Vec4( vnIni[0], -vnIni[1],  vnIni[2], -vnIni[3]),
                Vec4(-vnIni[0],  vnIni[1],  vnIni[2], -vnIni[3]),
                Vec4( vnIni[0], -vnIni[1], -vnIni[2],  vnIni[3]), # this might be used later for e3
                # I don't think these are necessary:
                #Vec4(-vnIni[0],  vnIni[1], -vnIni[2],  vnIni[3]),
                #Vec4(-vnIni[0], -vnIni[1],  vnIni[2],  vnIni[3])
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
    #print 'e3', this.e3
    return (e2, e3)

class DoubleRot4(Transform4):
    def __new__(this, quatPair = None,
        axialPlane = (Vec4([0, 0, 1, 0]), Vec4([0, 0, 0, 1])),
        angle = (0, 0)
    ):
        orthoPlane = findOrthoPlane(axialPlane)
        r0 = Rot4(axialPlane = axialPlane, angle = angle[0])
        r1 = Rot4(axialPlane = orthoPlane, angle = angle[1])
        return Transform4.__new__(this, [ r1[0]*r0[0], r0[1]*r1[1] ])

# TODO implement Geom3D.Line3D here (in this file)

# forced to use some matrix functions and don't want to add a dependency on a
# big python package.

class Mat(list):
    def __init__(this, m = None, id = 3):
        if m == None:
            m = []
            assert id > 0
            for i in range(id):
                v = []
                for j in range(id):
                    if i == j: v.append(1)
                    else:      v.append(0)
                m.append(Vec(v))
        this.rows = len(m)
        assert this.rows > 0
        this.cols = len(m[0])
        for row in m:
            assert isinstance(row, Vec)
            assert len(row) == this.cols
        list.__init__(this, m)

    def __str__(m):
        s = ''
        for row in m: s = '%s\n%s' % (s, str(row))
        return s

    def row(m, i):
        return m[i]

    def col(m, i):
        return Vec([row[i] for row in m])

    def transpose(m):
        return Mat([m.col(i) for i in range(m.cols)])

    T = transpose

    def deleteRow(m, i):
        # don't use m.pop(i), it changes m, while the result should be returned
        # instead.
        if i < 0: i += m.rows
        assert i >= 0
        n = m[0:i]
        n.extend(m[i+1:])
        return Mat(n)

    def deleteCol(m, i):
        if i < 0: i += m.cols
        assert i >= 0
        n = []
        for row in m:
            r = list(row[0:i])
            r.extend(list(row[i+1:]))
            n.append(Vec(r))
        return Mat(n)

    def replaceCol(m, i, v):
        assert len(v) == m.rows
        if i < 0: i += m.cols
        assert i >= 0
        n = []
        for k, row in zip(range(m.rows), m):
            r = list(row[0:i])
            r.append(v[k])
            r.extend(list(row[i+1:]))
            n.append(Vec(r))
        return Mat(n)

    def minor(m, i, j):
        return m.deleteRow(i).deleteCol(j).det()

    def orthogonal(m):
        return abs(m.det()) == 1

    def det(m):
        assert m.rows == m.cols
        if m.rows == 1: return m[0][0]
        #else:
        r = 0
        sign = 1
        for i, e in zip(range(m.cols), m[0]):
            if not eq(m[0][i], 0):
                r += sign * m[0][i] * m.minor(0, i)
            sign = -sign
        return r

    def __mul__(m, n):
        if isinstance(n, Mat):
            assert m.rows == n.cols
            assert n.rows == m.cols
            nT = n.T()
            return Mat([ Vec([row * col for col in nT]) for row in m ])
        elif isinstance(n, Vec):
            assert m.rows == len(n)
            return Vec([row * n for row in m])
        else:
            assert False, 'oops, unknown type of object to multiply matrix: %s.' % n

    def inverse(m):
        if m.orthogonal(): return m.T()
        else:
            # the hard way:
            det = m.det()
            sign = 1
            n = []
            for i in range(m.rows):
                r = []
                for j in range(m.cols):
                    r.append(sign * m.minor(i, j) / det)
                    sign = -sign
                n.append(Vec(r))
        return Mat(n).T()

    def solve(m, v):
        # use Cramer's method
        assert len(v) == m.rows
        det = m.det()
        return Vec([
                m.replaceCol(i, v).det() / det for i in range(m.cols)
            ])

    def stdRowShape(m, v):
        pass

if __name__ == '__main__':

    #####################
    # Vec
    #####################
    r = Vec([])
    assert(r == []), 'got %s instead' % str(r)

    v = Vec([1, 2, 4])
    w = Vec([2, 3, 5, 6])

    r = -v
    assert(r == Vec([-1.0, -2.0, -4.0])), 'got %s instead' % str(r)
    assert(type(r) == type(Vec([])))

    r = v+w
    assert(r == Vec([3.0, 5.0, 9.0])), 'got %s instead' % str(r)
    assert(type(r) == type(Vec([])))

    r = w-v
    assert(r == Vec([1.0, 1.0, 1.0])), 'got %s instead' % str(r)
    assert(type(r) == type(Vec([])))

    r = v*2
    assert(r == Vec([2.0, 4.0, 8.0])), 'got %s instead' % str(r)
    assert(type(r) == type(Vec([])))

    r = 2*v
    assert(r == Vec([2.0, 4.0, 8.0])), 'got %s instead' % str(r)
    assert(type(r) == type(Vec([])))

    r = v/2
    assert(r == Vec([0.5, 1.0, 2.0])), 'got %s instead' % str(r)
    assert(type(r) == type(Vec([])))

    #v[1] = 5.0
    #assert(v == Vec([1.0, 5.0, 4.0])), 'got %s instead' % v
    #assert(type(v) == type(Vec([])))

    v = Vec([1.0, 5.0, 4.0])
    r = v[1:]
    assert(r == Vec([5.0, 4.0])), 'got %s instead' % str(r)
    # TODO: howto without using deprecated __setslice__ ?
    # currently no problem, since r + w becomes a Vec anyway,
    # though 3 * r gives unexpected result
    #assert(type(r) == type(Vec([])))

    v =Vec([1, 2, 4])
    r = v.norm()
    assert(r == math.sqrt(1+4+16)), 'got %s instead' % str(r)

    v = Vec([3, 4, 5])
    n = v.norm()
    r = v.normalize()
    assert(r == Vec([v[0]/n, v[1]/n, v[2]/n])), 'got %s instead' % str(r)
    assert(type(r) == type(Vec([])))

    r = v.normalise()
    assert(r == Vec([v[0]/n, v[1]/n, v[2]/n])), 'got %s instead' % str(r)
    assert(type(r) == type(Vec([])))

    v = Vec([0, 0, 0])
    w = Vec([10, 0, 0])
    try:
        r = v.angle(w)
        assert False, 'exptected ZeroDivisionError: got %s instead' % str(r)
    except ZeroDivisionError:
        pass

    v = Vec([10, 0, 0])
    w = Vec([0, 0, 0])
    try:
        r = v.angle(w)
        assert False, 'exptected ZeroDivisionError: got %s instead' % str(r)
    except ZeroDivisionError:
        pass

    v = Vec([0, 0, 0])
    w = Vec([0, 0, 0])
    try:
        r = v.angle(w)
        assert False, 'exptected ZeroDivisionError: got %s instead' % str(r)
    except ZeroDivisionError:
        pass

    v = Vec([4, 0, 0])
    w = Vec([10, 0, 0])
    r = v.angle(w)
    assert(r == 0), 'got %s instead' % str(r)

    v = Vec([10, 0, 0])
    w = Vec([0, 3, 0])
    r = v.angle(w)
    assert(r == qTurn), 'got %s instead' % str(r)

    v = Vec([0, 10, 0])
    w = Vec([0, 3, 3])
    r = v.angle(w)
    assert(r == math.pi/4), 'got %s instead' % str(r)

    v = Vec([0, 10, 0])
    w = Vec([0, -3, 0])
    r = v.angle(w)
    assert(r == hTurn), 'got %s instead' % str(r)

    # Vec3
    v = Vec3([1,  2, 3])
    w = Vec3([2, -3, 4])
    r = v.cross(w)
    assert(r == Vec3([17, 2, -7])), 'got %s instead' % str(r)
    assert(type(r) == type(v))

    v = Vec3([1, 0, 0])
    w = Vec3([1, 0, 0])
    r = v.cross(w)
    assert(r == Vec3([0, 0, 0])), 'got %s instead' % str(r)
    assert(type(r) == type(v))

    v = Vec3([0, 0, 0])
    w = Vec3([1, 0, 0])
    r = v.cross(w)
    assert(r == Vec3([0, 0, 0])), 'got %s instead' % str(r)
    assert(type(r) == type(v))

    v = Vec3([1, 0, 0])
    w = Vec3([0, 0, 0])
    r = v.cross(w)
    assert(r == Vec3([0, 0, 0])), 'got %s instead' % str(r)
    assert(type(r) == type(v))

    v = Vec3([0, 0, 0])
    w = Vec3([0, 0, 0])
    r = v.cross(w)
    assert(r == Vec3([0, 0, 0])), 'got %s instead' % str(r)
    assert(type(r) == type(v))

    #####################
    # Quat
    #####################
    q0 = Quat([1, 2, 3, 5])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([-40, 8, 19, 9])), 'got %s instead' % str(r)
    assert(type(r) == type(q0))

    q0 = Quat([0, 0, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([0, 0, 0, 0])), 'got %s instead' % str(r)
    assert(type(r) == type(q0))

    q0 = Quat([1, 0, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([2, 4, 3, 5])), 'got %s instead' % str(r)
    assert(type(r) == type(q0))

    q0 = Quat([0, 1, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([-4, 2, -5, 3])), 'got %s instead' % str(r)
    assert(type(r) == type(q0))

    q0 = Quat([0, 0, 1, 0])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([-3, 5, 2, -4])), 'got %s instead' % str(r)
    assert(type(r) == type(q0))

    q0 = Quat([0, 0, 0, 1])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([-5, -3, 4, 2])), 'got %s instead' % str(r)
    assert(type(r) == type(q0))

    q = Quat([2, 4, 3, 5])
    r = q.S()
    assert(r == 2), 'got %s instead' % str(r)
    assert(type(r) == float)
    r = q.V()
    assert (r == Vec3([4, 3, 5])), 'got %s instead' % str(r)
    assert isinstance(r, Vec)

    q = Quat([2, 4, 3, 5])
    r = q.conjugate()
    assert(r == Quat([2, -4, -3, -5])), 'got %s instead' % str(r)
    assert(type(r) == type(q))

    q = Quat([2, 0, 0, 5])
    r = q.conjugate()
    assert(r == Quat([2, 0, 0, -5])), 'got %s instead' % str(r)
    assert(type(r) == type(q))

    q = Quat([0, 0, 0, 0])
    r = q.conjugate()
    assert(r == q), 'got %s instead' % str(r)
    assert(type(r) == type(q))

    #####################
    # Transform: Rot3
    #####################

    r = I * I
    assert(I != E), "This shouldn't hold %s != %s" % (I, E)
    assert(r == E), 'got %s instead' % str(r)

    q0 = Rot3(axis = uz, angle = 0)
    q1 = Rot3(axis = uz, angle = 2*math.pi)
    assert q0 == q1, "%s should = %s" % (str(q0), str(q1))

    q0 = Rot3(axis = uz, angle = math.pi)
    q1 = Rot3(axis = uz, angle = -math.pi)
    assert q0 == q1, "%s should = %s" % (str(q0), str(q1))

    r = Rot3(axis = Vec3([0, 0, 0]), angle = 0)
    assert(r[1] == Quat([1, 0, 0, 0])), 'got %s instead' % r[1]
    assert(r[0] == Quat([1, 0, 0, 0])), 'got %s instead' % r[0]

    #for a, b, in zip(r[1], Quat([1, 0, 0, 0])):
    #    print '%0.15f' % (a - b)

    # rotation around z -axis
    # 0 degrees (+/- 360)
    q = Rot3(axis = uz, angle = 0)
    v = Vec3(ux)
    r = q*v
    assert(r == ux), 'got %s instead' % str(r)

    # same as above but specifying the axis as a list
    q = Rot3(axis = [0, 0, 1], angle = 0)
    v = Vec3(ux)
    r = q*v
    assert(r == ux), 'got %s instead' % str(r)

    q = Rot3(axis = uz, angle = fullTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == ux), 'got %s instead' % str(r)

    q = Rot3(axis = uz, angle = -fullTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == ux), 'got %s instead' % str(r)

    # 90 degrees (+/- 360)
    q = Rot3(axis = uz, angle = qTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == uy), 'got %s instead' % str(r)

    q = Rot3(axis = uz, angle = qTurn + fullTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == uy), 'got %s instead' % str(r)

    q = Rot3(axis = uz, angle = qTurn - fullTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == uy), 'got %s instead' % str(r)

    # 180 degrees (+/- 360)
    q = Rot3(axis = uz, angle = hTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == -ux), 'got %s instead' % str(r)

    q = Rot3(axis = uz, angle = hTurn + fullTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == -ux), 'got %s instead' % str(r)

    q = Rot3(axis = uz, angle = hTurn - fullTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == -ux), 'got %s instead' % str(r)

    # -90 degrees (+/- 360)
    q = Rot3(axis = uz, angle = -qTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == -uy), 'got %s instead' % str(r)

    q = Rot3(axis = uz, angle = -qTurn + fullTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == -uy), 'got %s instead' % str(r)

    q = Rot3(axis = uz, angle = -qTurn - fullTurn)
    v = Vec3(ux)
    r = q*v
    assert(r == -uy), 'got %s instead' % str(r)

    # Quadrant I
    hV3 = math.sqrt(3) / 2
    q = Rot3(axis = uz, angle = math.pi/3)
    v = ux + 3*uz
    r = q*v
    assert(r == Vec3([0.5, hV3, 3])), 'got %s instead' % str(r)

    # Quadrant II
    q = Rot3(axis = uz, angle = hTurn - math.pi/3)
    v = ux + 3*uz
    r = q*v
    assert(r == Vec3([-0.5, hV3, 3])), 'got %s instead' % str(r)

    # Quadrant III
    q = Rot3(axis = uz, angle = math.pi + math.pi/3)
    v = ux + 3*uz
    r = q*v
    assert(r == Vec3([-0.5, -hV3, 3])), 'got %s instead' % str(r)

    # Quadrant IV
    q = Rot3(axis = uz, angle = - math.pi/3)
    v = ux + 3*uz
    r = q*v
    assert(r == Vec3([0.5, -hV3, 3])), 'got %s instead' % str(r)

    # 3D Quadrant I: rotation around (1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([1, 1, 1]), angle = tTurn)
    v = Vec3([-1, 1, 1])
    r = q*v
    assert(r == Vec3([1, -1, 1])), 'got %s instead' % str(r)
    # neg angle
    q = Rot3(axis = Vec3([1, 1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([1, 1, -1])), 'got %s instead' % str(r)
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([1, 1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([1, -1, 1])), 'got %s instead' % str(r)
    # neg axis
    q = Rot3(axis = -Vec3([1, 1, 1]), angle = tTurn)
    r = q*v
    assert(r == Vec3([1, 1, -1])), 'got %s instead' % str(r)

    # 3D Quadrant II: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([-1, 1, 1]), angle = tTurn)
    v = Vec3([1, 1, 1])
    r = q*v
    assert(r == Vec3([-1, 1, -1])), 'got %s instead' % str(r)
    # neg angle
    q = Rot3(axis = Vec3([-1, 1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % str(r)
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([-1, 1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([-1, 1, -1])), 'got %s instead' % str(r)
    # neg axis
    q = Rot3(axis = -Vec3([-1, 1, 1]), angle = tTurn)
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % str(r)

    # 3D Quadrant III: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([-1, -1, 1]), angle = tTurn)
    v = Vec3([1, 1, 1])
    r = q*v
    assert(r == Vec3([-1, 1, -1])), 'got %s instead' % str(r)
    # neg angle
    q = Rot3(axis = Vec3([-1, -1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % str(r)
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([-1, -1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([-1, 1, -1])), 'got %s instead' % str(r)
    # neg axis
    q = Rot3(axis = -Vec3([-1, -1, 1]), angle = tTurn)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % str(r)

    # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([1, -1, 1]), angle = tTurn)
    v = Vec3([1, 1, 1])
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % str(r)
    # neg angle
    q = Rot3(axis = Vec3([1, -1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % str(r)
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([1, -1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % str(r)
    # neg axis
    q = Rot3(axis = -Vec3([1, -1, 1]), angle = tTurn)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % str(r)

    # test quat mul from above (instead of Vec3):
    # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([1, -1, 1]), angle = tTurn)
    v = Quat([0, 1, 1, 1])
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % str(r)
    # neg angle
    q = Rot3(axis = Vec3([1, -1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % str(r)
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([1, -1, 1]), angle = -tTurn)
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % str(r)
    # neg axis
    q = Rot3(axis = -Vec3([1, -1, 1]), angle = tTurn)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % str(r)

    # Axis Angle:
    v = Vec3([1, -1, 1])
    a = tTurn
    t = Rot3(axis = v, angle = a)
    rx = t.axis()
    x = v.normalise()
    ra = t.angle()
    assert (
            (eq(ra, a) and rx == x)
            or
            (eq(ra, -a) and rx == -x)
        ), 'got (%s, %s) instead of (%s, %s) or (%s, %s)' % (
            ra, rx, a, x, -a, -x
        )
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # neg angle
    v = Vec3([1, -1, 1])
    a = -tTurn
    t = Rot3(axis = v, angle = a)
    rx = t.axis()
    x = v.normalise()
    ra = t.angle()
    assert (
            (eq(ra, a) and rx == x)
            or
            (eq(ra, -a) and rx == -x)
        ), 'got (%s, %s) instead of (%s, %s) or (%s, %s)' % (
            ra, rx, a, x, -a, -x
        )
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # neg angle, neg axis
    v = Vec3([-1, 1, -1])
    a = -tTurn
    t = Rot3(axis = v, angle = a)
    rx = t.axis()
    x = v.normalise()
    ra = t.angle()
    assert (
            (eq(ra, a) and rx == x)
            or
            (eq(ra, -a) and rx == -x)
        ), 'got (%s, %s) instead of (%s, %s) or (%s, %s)' % (
            ra, rx, a, x, -a, -x
        )
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # neg axis
    v = Vec3([-1, 1, -1])
    a = tTurn
    t = Rot3(axis = v, angle = a)
    rx = t.axis()
    x = v.normalise()
    ra = t.angle()
    assert (
            (eq(ra, a) and rx == x)
            or
            (eq(ra, -a) and rx == -x)
        ), 'got (%s, %s) instead of (%s, %s) or (%s, %s)' % (
            ra, rx, a, x, -a, -x
        )
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # Q I
    v = Vec3([-1, 1, -1])
    a = math.pi/3
    t = Rot3(axis = v, angle = a)
    rx = t.axis()
    x = v.normalise()
    ra = t.angle()
    assert (
            (eq(ra, a) and rx == x)
            or
            (eq(ra, -a) and rx == -x)
        ), 'got (%s, %s) instead of (%s, %s) or (%s, %s)' % (
            ra, rx, a, x, -a, -x
        )
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # Q II
    v = Vec3([-1, 1, -1])
    a = math.pi - math.pi/3
    t = Rot3(axis = v, angle = a)
    rx = t.axis()
    x = v.normalise()
    ra = t.angle()
    assert (
            (eq(ra, a) and rx == x)
            or
            (eq(ra, -a) and rx == -x)
        ), 'got (%s, %s) instead of (%s, %s) or (%s, %s)' % (
            ra, rx, a, x, -a, -x
        )
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # Q III
    v = Vec3([-1, 1, -1])
    a = math.pi + math.pi/3
    t = Rot3(axis = v, angle = a)
    rx = t.axis()
    x = v.normalise()
    ra = t.angle()
    assert (
            (eq(ra, a) and rx == x)
            or
            (eq(ra, -a) and rx == -x)
        ), 'got (%s, %s) instead of (%s, %s) or (%s, %s)' % (
            ra, rx, a, x, -a, -x
        )
    assert t.isRot()
    assert not t.isRefl()
    assert not t.isRotInv()
    assert t.type() == t.Rot
    # Q IV
    v = Vec3([-1, 1, -1])
    a = - math.pi/3
    t = Rot3(axis = v, angle = a)
    rx = t.axis()
    x = v.normalise()
    ra = t.angle()
    assert (
            (eq(ra, a) and rx == x)
            or
            (eq(ra, -a) and rx == -x)
        ), 'got (%s, %s) instead of (%s, %s) or (%s, %s)' % (
            ra, rx, a, x, -a, -x
        )
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
    r0 = Rot3(axis = Vec3([1, 2, 3]), angle = 2)
    r1 = Rot3(-r0[0])
    assert r0 == r1

    # test order
    r0 = Rot3(axis = uz, angle = qTurn)
    r1 = Rot3(axis = ux, angle = qTurn)
    r = (r1 * r0) * ux # expected: r1(r0(x))
    assert r == uz, 'Expected: %s, got %s' % (uz, r)
    r = (r1 * r0)
    x = Rot3(axis = Vec3([1, -1, 1]), angle = tTurn)
    assert r == x, 'Expected: %s, got %s' % (x, r)
    r = (r0 * r1)
    x = Rot3(axis = Vec3([1, 1, 1]), angle = tTurn)
    assert r == x, 'Expected: %s, got %s' % (x, r)

    # test conversion to Mat
    # x-axis
    r = Rot3(axis = uz, angle = qTurn).matrix()
    # 0  -1  0
    # 1   0  0
    # 0   0  1
    x = Vec3([0, -1, 0])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([1, 0, 0])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([0, 0, 1])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])
    r = Rot3(axis = uz, angle = hTurn).matrix()
    # -1   0  0
    #  0  -1  0
    #  0   0  1
    x = Vec3([-1, 0, 0])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([0, -1, 0])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([0, 0, 1])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])
    r = Rot3(axis = uz, angle = -qTurn).matrix()
    #  0   1  0
    # -1   0  0
    #  0   0  1
    x = Vec3([ 0, 1, 0])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([-1, 0, 0])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([0, 0, 1])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])

    # y-axis
    r = Rot3(axis = uy, angle = qTurn).matrix()
    #  0   0   1
    #  0   1   0
    # -1   0   0
    x = Vec3([ 0, 0,  1])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([ 0, 1, 0])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([-1, 0, 0])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])
    r = Rot3(axis = uy, angle = hTurn).matrix()
    # -1   0   0
    #  0   1   0
    #  0   0  -1
    x = Vec3([-1, 0, 0])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([0,  1, 0])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([0, 0, -1])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])
    r = Rot3(axis = uy, angle = -qTurn).matrix()
    #  0   0  -1
    #  0   1   0
    #  1   0   0
    x = Vec3([ 0, 0, -1])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([ 0, 1,  0])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([ 1, 0,  0])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])

    # x-axis
    r = Rot3(axis = ux, angle = qTurn).matrix()
    # 1  0  0
    # 0  0 -1
    # 0  1  0
    x = Vec3([1,  0, 0])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([0,  0, -1])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([0,  1,  0])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])
    r = Rot3(axis = ux, angle = hTurn).matrix()
    #  1  0  0
    #  0 -1  0
    #  0  0 -1
    x = Vec3([1,  0,  0])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([0, -1,  0])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([0,  0, -1])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])
    r = Rot3(axis = ux, angle = -qTurn).matrix()
    #  1  0  0
    #  0  0  1
    #  0 -1  0
    x = Vec3([ 1,  0,  0])
    assert r[0] == x, 'Expected: %s, got %s' % (x, r[0])
    x = Vec3([ 0,  0,  1])
    assert r[1] == x, 'Expected: %s, got %s' % (x, r[1])
    x = Vec3([ 0, -1,  0])
    assert r[2] == x, 'Expected: %s, got %s' % (x, r[2])

    from random import seed, random
    seed(700114) # constant seed to be able to catch errors
    for i in range(100):
        r0 = Rot3(
                axis = [2*random()-1, 2*random()-1, 2*random()-1],
                angle = random() * 2 * math.pi
            )
        r1 = Rot3(
                axis = [2*random()-1, 2*random()-1, 2*random()-1],
                angle = random() * 2 * math.pi
            )
        r = r0 * r1
        assert r0.isRot()
        assert not r0.isRefl()
        assert not r0.isRotInv()
        assert r1.isRot()
        assert not r1.isRefl()
        assert not r1.isRotInv()
        assert r.isRot()
        assert not r.isRefl()
        assert not r.isRotInv()
        assert r0 * r0.inverse() == E
        assert r1 * r1.inverse() == E
        assert r * r.inverse() == E

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
        v = Vec3([0, 0, 0])
        Refl3(planeN = v)
        assert False
    except AssertionError:
        pass

    try:
        v = Vec3([1, 0, 0, 0])
        Refl3(planeN = v)
        assert False
    except AssertionError:
        pass

    try:
        v = Vec([1, 0])
        Refl3(planeN = v)
        assert False
    except IndexError:
        pass

    from random import seed, random
    seed(700114) # constant seed to be able to catch errors
    for i in range(100):
        s0 = Refl3(planeN = Vec3([2*random()-1, 2*random()-1, 2*random()-1]))
        s1 = Refl3(planeN = Vec3([2*random()-1, 2*random()-1, 2*random()-1]))
        r = s0 * s1
        assert not s0.isRot()
        assert s0.isRefl()
        assert not s0.isRotInv(), "for i = %d: %s" % (i, str(s0))
        assert not s1.isRot()
        assert s1.isRefl()
        assert not s1.isRotInv()
        assert r.isRot()
        assert not r.isRefl()
        assert not r.isRotInv()
        assert (s0 * s0) == E, 'for i == %d' % i
        assert (s1 * s1) == E, 'for i == %d' % i
        assert r * r.inverse() == E

    # border cases
    s0 = Refl3(planeN = ux)
    s1 = Refl3(planeN = uy)
    r = s0 * s1
    assert r.isRot()
    assert not r.isRefl()
    assert not r.isRotInv()
    assert r == HalfTurn3(uz)
    r = s1 * s0
    assert r.isRot()
    assert not r.isRefl()
    assert not r.isRotInv()
    assert r == HalfTurn3(uz)

    s0 = Refl3(planeN = ux)
    s1 = Refl3(planeN = uz)
    r = s0 * s1
    assert r.isRot()
    assert not r.isRefl()
    assert not r.isRotInv()
    assert r == HalfTurn3(uy)
    r = s1 * s0
    assert r.isRot()
    assert not r.isRefl()
    assert not r.isRotInv()
    assert r == HalfTurn3(uy)

    s0 = Refl3(planeN = uy)
    s1 = Refl3(planeN = uz)
    r = s0 * s1
    assert r.isRot()
    assert not r.isRefl()
    assert not r.isRotInv()
    assert r == HalfTurn3(ux)
    r = s1 * s0
    assert r.isRot()
    assert not r.isRefl()
    assert not r.isRotInv()
    assert r == HalfTurn3(ux)

    s0 = Refl3(planeN = ux)
    s1 = Refl3(planeN = uy)
    s2 = Refl3(planeN = uz)
    r = s0 * s1 * s2
    assert not r.isRot()
    assert not r.isRefl()
    assert r.isRotInv()
    assert r == I

    # test order: 2 refl planes with 45 degrees in between: 90 rotation
    s0 = Refl3(planeN = Vec3([0, 3, 0]))
    s1 = Refl3(planeN = Vec3([-1, 1, 0]))
    r = (s1 * s0)
    x = Rot3(axis = uz, angle = qTurn)
    assert r == x, 'Expected: %s, got %s' % (x, r)
    r = (s0 * s1)
    x = Rot3(axis = uz, angle = -qTurn)
    assert r == x, 'Expected: %s, got %s' % (x, r)

    # tests eq reflection for opposite normals
    seed(760117) # constant seed to be able to catch errors
    for i in range(100):
        N = Vec3([2*random()-1, 2*random()-1, 2*random()-1])
        s0 = Refl3(planeN = N)
        s1 = Refl3(planeN = -N)
        assert s0 == s1, '%s should == %s (i=%d)' % (s0, s1, i)
        r = s0 * s1
        assert r == E, 'refl*refl: %s should == %s (i=%d)' % (r, E, i)

    # reflection in same plane: border cases
    bCases = [ux, uy, uz]
    for N in bCases:
        s0 = Refl3(planeN = N)
        s1 = Refl3(planeN = -N)
        assert s0 == s1, '%s should == %s (i=%d)' % (s0, s1, i)
        r = s0 * s1
        assert r == E, 'refl*refl: %s should == %s (i=%d)' % (r, E, i)

    #####################
    # Transform: Rotary inversion
    #####################

    # type: r*I == I*r and gives a rotary inversion (random)

    from random import seed, random
    seed(700114) # constant seed to be able to catch errors
    for i in range(100):
        r0 = RotInv3(
                axis = [2*random()-1, 2*random()-1, 2*random()-1],
                angle = random() * 2 * math.pi
            )
        r1 = RotInv3(
                axis = [2*random()-1, 2*random()-1, 2*random()-1],
                angle = random() * 2 * math.pi
            )
        r = r0 * r1
        assert not r0.isRot()
        assert not r0.isRefl()
        assert r0.isRotInv()
        assert not r1.isRot()
        assert not r1.isRefl()
        assert r1.isRotInv()
        assert r.isRot()
        assert not r.isRefl()
        assert not r.isRotInv()
        assert r0 * r0.inverse() == E
        assert r1 * r1.inverse() == E
        assert r * r.inverse() == E

    #####################
    # Rot4:
    #####################
    r0 = Rot4(axialPlane = (Vec4([1, 0, 0, 0]), Vec4([0, 0, 0, 1])), angle = math.pi/3)
    v = Vec4([10, 2, 0, 6])
    r = r0 * v
    x = Quat([v[0], 1, -math.sqrt(3), v[3]])
    eqFloatMargin = 1.0e-14
    assert r == x, 'Expected: %s, got %s' % (x, r)

    from random import seed, random
    seed(700114) # constant seed to be able to catch errors
    for i in range(100):
        x0 = Vec4([2*random()-1, 2*random()-1, 2*random()-1, 2*random()-1])
        # make sure orthogonal: x0*x1 + y0*y1 + z0*z1 + w0*w1 == 0
        w, x, y = (2*random()-1, 2*random()-1, 2*random()-1)
        z = (-w*x0[0] - x*x0[1] - y*x0[2])/ x0[3]
        x1 = Vec4([w, x, y, z])
        r0 = Rot4(axialPlane = (x0, x1), angle = random() * 2 * math.pi)
        x0 = Vec4([2*random()-1, 2*random()-1, 2*random()-1, 2*random()-1])
        w, x, y = (2*random()-1, 2*random()-1, 2*random()-1)
        # make sure orthogonal: x0*x1 + y0*y1 + z0*z1 + w0*w1 == 0
        z = (-w*x0[0] - x*x0[1] - y*x0[2])/ x0[3]
        x1 = Vec4([w, x, y, z])
        r1 = Rot4(axialPlane = (x0, x1), angle = random() * 2 * math.pi)
        r = r0 * r1
        assert r0.isRot()
        #assert not r0.isRefl()
        #assert not r0.isRotInv()
        assert r1.isRot()
        #assert not r1.isRefl()
        #assert not r1.isRotInv()
        assert r.isRot()
        #assert not r.isRefl()
        #assert not r.isRotInv()
        #assert r0 * r0.inverse() == E
        #assert r1 * r1.inverse() == E
        #assert r * r.inverse() == E
        for n in range(1, 12):
            #print 'n', n
            if n > 98: eqFloatMargin = 1.0e-12
            r0 = Rot4(axialPlane = (x0, x1), angle = 2 * math.pi / n)
            r = r0
            for j in range(1, n):
                a = r.angle()
                #print 'n:', n, 'j:', j, 'a:', a
                assert eq(j * 2 * math.pi / n, a), 'j: %d, r: %f' % (
                        j, 2 * math.pi / n / a
                    )
                r = r0 * r
            ra = r.angle()
            assert eq(ra, 0) or eq(ra, 2*math.pi), r.angle()

    #####################
    # DoubleRot4:
    #####################
    r0 = DoubleRot4(
            axialPlane = (Vec4([1, 0, 0, 0]), Vec4([0, 0, 0, 1])),
            angle = (math.pi/3, math.pi/4) # 1/6 th and 1/8 th turn
        )
    v = Vec4([6, 2, 0, 6])
    r = r0 * v
    x = Quat([0, 1, -math.sqrt(3), math.sqrt(72)])
    eqFloatMargin = 1.0e-14
    assert r0.isRot()
    assert r == x, 'Expected: %s, got %s' % (x, r)
    r = E
    for i in range(23):
        r = r0 * r
        oopsMsg = 'oops for i = %d' %  i
        assert r.isRot(), oopsMsg
        ra = r.angle()
        #print 'angle:', 180*ra / math.pi
        #print  r * v
        assert not eq(ra, 0) and not eq(ra, 2*math.pi), ra
    r = r0 * r
    assert r.isRot()
    ra = r.angle()
    #print 'angle:', 180*ra / math.pi
    #print  r * v
    assert eq(ra, 0) or eq(ra, 2*math.pi), r.angle()

    r0 = DoubleRot4(
            axialPlane = (Vec4([1, 0, 0, 0]), Vec4([0, 0, 0, 1])),
            angle = (math.pi/4, math.pi/3) # 1/6 th and 1/8 th turn
        )
    v = Vec4([6, 2, 2, 0])
    r = r0 * v
    x = Quat([3, math.sqrt(8), 0, 3*math.sqrt(3)])
    eqFloatMargin = 1.0e-14
    assert r0.isRot()
    assert r == x, 'Expected: %s, got %s' % (x, r)
    r = E
    for i in range(23):
        r = r0 * r
        oopsMsg = 'oops for i = %d' %  i
        assert r.isRot(), oopsMsg
        ra = r.angle()
        #print 'angle:', 180*ra / math.pi
        #print  r * v
        assert not eq(ra, 0) and not eq(ra, 2*math.pi), ra
    r = r0 * r
    assert r.isRot()
    ra = r.angle()
    #print 'angle:', 180*ra / math.pi
    #print  r * v
    assert eq(ra, 0) or eq(ra, 2*math.pi), r.angle()

    # test if vectors in axial plane are not changed.
    v0 = Vec4([1, 1, 1, 0])
    v1 = Vec4([0, 0, 1, 1])
    v1 = v1.makeOrthogonalTo(v0)
    r0 = DoubleRot4(
            axialPlane = (v1, v0),
            angle = (math.pi/4, math.pi/3) # 1/6 th and 1/8 th turn
        )
    for i in range(5):
        v = v0 + i * v1
        r = r0 * v
        x = v
        assert eq(ra, 0) or eq(ra, 2*math.pi), "%d: expected: %s, got: %s" % (i, x, r)
        v = i* v0 + v1
        r = r0 * v
        x = v
        assert eq(ra, 0) or eq(ra, 2*math.pi), "%d: expected: %s, got: %s" % (i, x, r)

    #####################
    # Mat
    #####################
    m = Mat([Vec([1, 2, 3]),
        Vec([0, 2, 1]),
        Vec([1, -1, 3])
      ])

    l = m.rows
    w = m.cols

    assert m.det() == m.T().det()
    assert m == m.T().T()

    t = m.T()

    for i in range(l):
        r = m.deleteRow(i)
        assert r.rows == l-1
        assert r.cols == w
        assert r == m.deleteRow(-(l-i))
        n = t.T()
        n.pop(i)
        assert r == n

    for i in range(w):
        r = m.deleteCol(i)
        assert r.rows == l
        assert r.cols == w-1
        assert r == m.deleteCol(-(w-i))
        t = m.T()
        t.pop(i)
        assert r == t.T()

    # don't want to test an orthogonal matrix,
    # since then the inverse method calls: det, deleteRow, -Col, and transpose.
    assert not m.orthogonal()
    mI = m.inverse()
    assert m * mI == Mat()
    assert mI * m == Mat()
    b = Vec([1, 2, 3])
    assert m.solve(b) == mI * b

    print 'success!'
