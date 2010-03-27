#! /usr/bin/python

import math

turn      = lambda r: r * 2 * math.pi
degrees   = lambda r: math.pi * r / 180
toDegrees = lambda r: 180.0 * r   / math.pi

fullTurn = turn(1)
hTurn    = turn(0.5)
qTurn    = turn(0.25)
tTurn    = turn(1.0/3)

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

# Use tuples instead of lists to enable building sets used for isometries

class Vec(tuple):
    eqMargin = defaultFloatMargin

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
            print 'info: comparing different types in Vec (%s and %s)' % (
                    v.__class__.__name__, w.__class__.__name__
                )
            return False
        for a, b in zip(v, w):
            if not r: break
            r = r and eq(a, b, v.eqMargin)
            #print '%s ?= %s : %s' % (a, b, eq(a, b, v.eqMargin))
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

    def norm(v):
        r = 0
        for a in v: r += a*a
        return math.sqrt(r)

    def normalise(v):
        return v/v.norm()

    normalize = normalise
    N = normalise

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

    def scalar(v):
        """Returns the scalar part of v"""
        return v[0]

    def vector(v):
        """Returns the vector part of v (as a Vec3)"""
        return Vec3(v[1:])

    S = scalar
    V = vector

def transform3TypeStr(i):
    if i == Transform3.Rot:    return 'Rot3'
    if i == Transform3.Refl:   return 'Refl3'
    if i == Transform3.RotInv: return 'RotInv3'
    else:                      return 'Transform3'

class Transform3():
    def __init__(this, qLeft, qRight):
        this.left = qLeft
        this.right = qRight

    def __repr__(t):
        return '%s(%s, %s)' % (transform3TypeStr(t.type()), t.left, t.right)

    def __str__(t):
        if t.isRot(): return t.__strRot()
        elif t.isRefl(): return t.__strRefl()
        elif t.isRotInv(): return t.__strRotInv()
        else:
            return '%s * .. * %s' % (t.left, t.right)

    def __mul__(t, u):
        if isinstance(u, Transform3):
            # t * u =  wLeft * vLeft .. vRight * wRight
            return Transform3(t.left * u.left, u.right * t.right)
        # TODO: check kind of Transform3 and optimise
        elif isinstance(u, Vec) and len(u) == 3:
            return (t.left * Quat([0, u[0], u[1], u[2]]) * t.right).V()
        elif isinstance(u, Quat):
            return (t.left * u                           * t.right).V()
        else:
            raise TypeError, "unsupported op type(s) for *: '%s' and '%s'" % (
                    t.__class__.__name__, u.__class__.__name__
                )

    def __eq__(t, u):
        if not isinstance(u, Transform3): return False
        if t.isRot() and u.isRot: return t.__eqRot(u)
        elif t.isRefl() and u.isRefl: return t.__eqRefl(u)
        elif t.isRotInv() and u.isRotInv: return t.__eqRotInv(u)
        else:
            return (t.left == u.left and t.right == u.right)

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
        assert False, 'oops, unknown type of Transform: %s ?= 1' % t.right.norm()
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
        if t.isRot(): return t.matrixRot()
        assert False, (
            'oops, unknown matrix; transform %s\n' +
            'not a rotation' % t)

    ## ROTATION specific functions:
    def isRot(t):
        #print 't.right.conjugate() == t.left', t.right.conjugate() == t.left
        #print '%s = t.right.conjugate() == t.left %s ' % (
        #        t.right.conjugate(), t.left
        #    )
        #print '1 ?= t.right.norm() = %0.17f' % t.right.norm()
        #print '-1 ?<= t.S() = %0.17f ?<= 1' % t.right.S()
        return (
            t.right.conjugate() == t.left
            and
            eq(t.right.norm(), 1)
            and
            (t.right.S() < 1 or eq(t.right.S(), 1))
            and
            (t.right.S() > -1 or eq(t.right.S(), -1))
        )

    def __eqRot(t, u):
        """Compare two transforms that represent rotations
        """
        return (
            (t.left == u.left and t.right == u.right)
            or
            # negative axis with negative angle:
            (t.left == -u.left and t.right == -u.right)
            or
            # half turn (equal angle) around opposite axes
            (eq(t.left[0], 0) and t.left == u.right)
        )

    def __strRot(t):
        str = 'Rotation of %s rad around %s' % (t.angleRot(), t.axisRot())
        return str

    def angleRot(t):
        cos = t.left[0]
        for i in range(3):
            try:
                sin = t.left[i+1] / t.left.V().N()[i]
                break
            except ZeroDivisionError:
                if i == 2:
                    assert ( t.left == Quat([1, 0, 0, 0]) or
                            t.left == Quat([-1, 0, 0, 0])
                        ), (
                            "%s doesn't represent a rotation" % t.__repr__()
                        )
                    return 0
        #print 'reconstructed cos =', cos
        #print 'reconstructed sin =', sin
        return 2 * math.atan2(sin, cos)

    def axisRot(t):
        try:
            return t.left.V().N()
        except ZeroDivisionError:
            assert (t.left == Quat([1, 0, 0, 0]) or
                    t.left == Quat([-1, 0, 0, 0])
                ), (
                    "%s doesn't represent a rotation" % t.__repr__()
                )
            return t.left.V()

    def matrixRot(t):
        w, x, y, z = t.left
        dxy, dxz, dyz = 2*x*y, 2*x*z, 2*y*z
        dxw, dyw, dzw = 2*x*w, 2*y*w, 2*z*w
        dx2, dy2, dz2 = 2*x*x, 2*y*y, 2*z*z
        return [
            Vec([1-dy2-dz2,     dxy-dzw,        dxz+dyw]),
            Vec([dxy+dzw,       1-dx2-dz2,      dyz-dxw]),
            Vec([dxz-dyw,       dyz+dxw,        1-dx2-dy2]),
        ]

    ## REFLECTION specific functions:
    def isRefl(t):
        #print 't.right == t.left:', t.right == t.left
        #print '1 ?= t.right.norm() = %0.17f' % t.right.norm()
        #print '0 ?= t.right.S() = %0.17f' % t.right.S()
        return (
            t.right == t.left
            and
            eq(t.right.norm(), 1)
            and
            eq(t.right.S(), 0)
        )

    def __eqRefl(t, u):
        """Compare two transforms that represent reflections
        """
        return (
            # not needed: and t.right == u.right)
            # since __eqRefl is called for t and u reflections
            (t.left == u.left)
            or
            (t.left == -u.left)
            # again not needed: and t.right == u.right)
        )

    def __strRefl(s):
        return 'Reflection in plane with normal %s' % (s.planeN())

    def planeN(s):
        return s.left.V()

    ## ROTARY INVERSION (= ROTARY RELECTION) specific functions:
    def I(t):
        """
        Apply a central inversion
        """
        return Transform3(-t.left, t.right)

    def isRotInv(t):
        return t.I().isRot()

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

    isRotRefl   = isRotInv
    axisRotRefl = axisRotInv

    def angleRotRefl(t):
        return (t.angleRotInv() - hTurn)

class Rot3(Transform3):
    def __init__(this, qLeft = None, axis = Vec3([1, 0, 0]), angle = 0):
        """
        Initialise a 3D rotation
        """
        if isinstance(qLeft, Quat):
            try: qLeft = qLeft.N()
            except ZeroDivisionError: pass # will fail on assert below:
            Transform3.__init__(this, qLeft, qLeft.conjugate())
            assert this.isRot(), "%s doesn't represent a rotation" % str(qLeft)
        else:
            # q = cos(angle) + y sin(angle)
            alpha = angle / 2
            if axis != Vec3([0, 0, 0]):
                axis = axis.N()
            q = math.sin(alpha) * axis
            q = Quat([math.cos(alpha), q[0], q[1], q[2]])
            #print 'cos =', math.cos(alpha)
            #print 'sin =', math.sin(alpha)
            Transform3.__init__(this, q, q.conjugate())

class HalfTurn3(Rot3):
    def __init__(this, axis):
        Rot3.__init__(this, axis = axis, angle = hTurn)

class Rotx(Rot3):
    def __init__(this, angle):
        Rot3.__init__(this, axis = ux, angle = angle)

class Roty(Rot3):
    def __init__(this, angle):
        Rot3.__init__(this, axis = uy, angle = angle)

class Rotz(Rot3):
    def __init__(this, angle):
        Rot3.__init__(this, axis = uz, angle = angle)

class Refl3(Transform3):
    def __init__(this, q = None, planeN = None):
        """Define a 3D reflection is a plane

        Either define
        q: quaternion representing the left (and right) quaternion
           multiplication for a reflection
        or
        planeN: the 3D normal of the plane in which the reflection takes place.
        """
        if isinstance(q, Quat):
            try: q = q.N()
            except ZeroDivisionError: pass # will fail on assert below:
            Transform3.__init__(this, q, q)
            assert this.isRefl(), "%s doesn't represent a reflection" % str(q)
        else:
            try:
                normal = planeN.N()
                q = Quat(normal)
            except ZeroDivisionError:
                q = Quat(planeN) # will fail on assert below:
            Transform3.__init__(this, q, q)
            assert this.isRefl(), (
                "normal %s doesn't define a valid 3D plane normal" % str(planeN)
            )

class RotInv3(Transform3):
    def __init__(this, qLeft = None, axis = None, angle = None):
        """
        Initialise a 3D rotation
        """
        # Do not inherit from Rot3 (and then apply inversion):
        # a rotary inversion is not a rotation.
        ri = Rot3(qLeft, axis, angle).I()
        Transform3.__init__(this, ri.left, ri.right)

RotRefl = RotInv3
I = RotInv3(Quat([1, 0, 0, 0]))
E = Rot3(Quat([1, 0, 0, 0]))
Hx = HalfTurn3(ux)
Hy = HalfTurn3(uy)
Hz = HalfTurn3(uz)

# TODO implement Geom3D.Line3D here (in this file)

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

    r = Rot3(axis = Vec3([0, 0, 0]), angle = 0)
    assert(r.right == Quat([1, 0, 0, 0])), 'got %s instead' % r.right
    assert(r.left == Quat([1, 0, 0, 0])), 'got %s instead' % r.left

    #for a, b, in zip(r.right, Quat([1, 0, 0, 0])):
    #    print '%0.15f' % (a - b)

    # rotation around z -axis
    # 0 degrees (+/- 360)
    q = Rot3(axis = uz, angle = 0)
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
    x = v.N()
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
    x = v.N()
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
    x = v.N()
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
    x = v.N()
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
    x = v.N()
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
    x = v.N()
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
    x = v.N()
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
    x = v.N()
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
    r1 = Rot3(-r0.left)
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
        assert r.isRot()
        assert not r.isRefl()
        assert not r.isRotInv()
        assert (s0 * s0) == E, 'for i == %d' % i
        assert (s1 * s1) == E, 'for i == %d' % i

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

    print 'succes'
