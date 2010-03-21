#! /usr/bin/python

import math

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

class Vec(list):
    eqMargin = defaultFloatMargin

    def __init__(this, v):
        list.__init__(this, [float(a) for a in v])

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
        r = len(v) == len(w)
        for a, b in zip(v, w): 
            if not r: break
            r = r and eq(a, b, v.eqMargin)
        return r

    def __ne__(v, w):
        return not(v == w)

    def __neg__(v):
        return v.__class__([-a for a in v])

    def __mul__(v, w):
        if isinstance(w, list):
            # dot product
            r = 0
            for a, b in zip(v, w): r += a*b
            return r
        elif isinstance(w, int) or isinstance(w, float):
            return v.__class__([w*a for a in v])

    def __rmul__(v, w):
        if isinstance(w, list):
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
    def __init__(this, v):
        Vec.__init__(this, [float(v[i]) for i in range(3)])

    def cross(v, w):
        return v.__class__([
                v[1] * w[2] - v[2] * w[1],
                v[2] * w[0] - v[0] * w[2],
                v[0] * w[1] - v[1] * w[0]
            ])

    # TODO implement Scenes3D.getAxis2AxisRotation here

class Quat(Vec):
    def __init__(this, v = None):
        Vec.__init__(this, [float(v[i]) for i in range(4)])

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

class Transform():
    def __init__(this, qLeft, qRight):
        this.left = qLeft
        this.right = qRight

    def __repr__(v):
        return '%s(%s, %s)' % (v.__class__.__name__, v.left, v.right)

    def __str__(v):
        return '%s * .. * %s' % (v.left, v.right)

    def __mul__(v, w):
        if isinstance(w, Transform):
            # v * w =  vLeft * wLeft .. wRight * vRight
            return Transform(v.left * w.left, w.right * v.right)
        elif isinstance(w, Vec) and len(w) == 3:
            # TODO: check kind of Transform
            return Vec3(v.left * Quat([0, w[0], w[1], w[2]]) * v.right)
        else:
            raise TypeError, "unsupported op type(s) for *: '%s' and '%s'" % (
                    v.__class__.__name__, w.__class__.__name__
                )

    def __eq__(v, w):
        return (v.left == w.left and v.right == w.right)

    def __ne__(v, w):
        return not(v == w)

    def isRot(this):
        return (
            v.right.conjugate() == v.left
            and
            v.right.N() == 1
            and
            v.S <= 1 and v.S >= -1
        )

    def isRefl(this):
        return (
            v.right.conjugate() == v.left
            and
            v.right.N() == 1
            and
            v.S == 0
        )

    def isRotInv(this):
        pass

    isRotRefl = isRotInv

class Rot(Transform):
    def __init__(this, v = None, axis = None, angle = None):
        # TODO: normalise
        Transform.__init__(this, v.conjugate(), v)

class HalfTurn(Rot):
    def __init__(this, axis):
        Rot.__init__(this, axis = axis, angle = math.pi)

class Refl(Transform):
    def __init__(this, q = None, normal = None):
        Transform.__init__(this, v)

class RotInv(Transform):
    def __init__(this, q = None, axis = None, angle = None):
        try:
            qLeft = -q.conjugate()
        except AttributeError:
            # in case q is a Vec
            q = Quat(q)
            qLeft = -q.conjugate()
        Transform.__init__(this, qLeft, q)

    def __str__(q):
        return '%s * .. * %s' % (q.left, q.right)

    def __repr__(q):
        return '%s(%s, %s)' % (q.__class__.__name__, q.left, q.right)

RotRefl = RotInv
I = RotInv(Quat([1, 0, 0, 0]))
E = Rot(Quat([1, 0, 0, 0]))

# TODO implement Geom3D.Line3D here (in this file)

if __name__ == '__main__':

    assert I.__repr__() == 'RotInv([-1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0])'

    r = Vec([])
    assert(r == []), 'got %s instead' % r

    v =Vec([1, 2, 4])
    w = Vec([2, 3, 5, 6])

    r = -v
    assert(r == Vec([-1.0, -2.0, -4.0])), 'got %s instead' % r
    assert(type(r) == type(Vec([])))

    r = v+w
    assert(r == Vec([3.0, 5.0, 9.0])), 'got %s instead' % r
    assert(type(r) == type(Vec([])))

    r = w-v
    assert(r == Vec([1.0, 1.0, 1.0])), 'got %s instead' % r
    assert(type(r) == type(Vec([])))

    r = v*2
    assert(r == Vec([2.0, 4.0, 8.0])), 'got %s instead' % r
    assert(type(r) == type(Vec([])))

    r = 2*v
    assert(r == Vec([2.0, 4.0, 8.0])), 'got %s instead' % r
    assert(type(r) == type(Vec([])))

    r = v/2
    assert(r == Vec([0.5, 1.0, 2.0])), 'got %s instead' % r
    assert(type(r) == type(Vec([])))

    v[1] = 5.0
    assert(v == Vec([1.0, 5.0, 4.0])), 'got %s instead' % v
    assert(type(v) == type(Vec([])))

    r = v[1:]
    assert(r == Vec([5.0, 4.0])), 'got %s instead' % r
    # TODO: howto without using deprecated __setslice__ ?
    # currently no problem, since r + w becomes a Vec anyway,
    # though 3 * r gives unexpected result
    #assert(type(r) == type(Vec([])))

    v =Vec([1, 2, 4])
    r = v.norm()
    assert(r == math.sqrt(1+4+16)), 'got %s instead' % r

    v = Vec([3, 4, 5])
    n = v.norm()
    r = v.normalize()
    assert(r == Vec([v[0]/n, v[1]/n, v[2]/n])), 'got %s instead' % r
    assert(type(r) == type(Vec([])))

    r = v.normalise()
    assert(r == Vec([v[0]/n, v[1]/n, v[2]/n])), 'got %s instead' % r
    assert(type(r) == type(Vec([])))

    v = Vec([0, 0, 0])
    w = Vec([10, 0, 0])
    try:
        r = v.angle(w)
        assert False, 'exptected ZeroDivisionError: got %s instead' % r
    except ZeroDivisionError:
        pass

    v = Vec([10, 0, 0])
    w = Vec([0, 0, 0])
    try:
        r = v.angle(w)
        assert False, 'exptected ZeroDivisionError: got %s instead' % r
    except ZeroDivisionError:
        pass

    v = Vec([0, 0, 0])
    w = Vec([0, 0, 0])
    try:
        r = v.angle(w)
        assert False, 'exptected ZeroDivisionError: got %s instead' % r
    except ZeroDivisionError:
        pass

    v = Vec([4, 0, 0])
    w = Vec([10, 0, 0])
    r = v.angle(w)
    assert(r == 0), 'got %s instead' % r

    v = Vec([10, 0, 0])
    w = Vec([0, 3, 0])
    r = v.angle(w)
    assert(r == math.pi/2), 'got %s instead' % r

    v = Vec([0, 10, 0])
    w = Vec([0, 3, 3])
    r = v.angle(w)
    assert(r == math.pi/4), 'got %s instead' % r

    v = Vec([0, 10, 0])
    w = Vec([0, -3, 0])
    r = v.angle(w)
    assert(r == math.pi), 'got %s instead' % r

    v = Vec3([1,  2, 3])
    w = Vec3([2, -3, 4])
    r = v.cross(w)
    assert(r == Vec3([17, 2, -7])), 'got %s instead' % r
    assert(type(r) == type(v))

    v = Vec3([1, 0, 0])
    w = Vec3([1, 0, 0])
    r = v.cross(w)
    assert(r == Vec3([0, 0, 0])), 'got %s instead' % r
    assert(type(r) == type(v))

    v = Vec3([0, 0, 0])
    w = Vec3([1, 0, 0])
    r = v.cross(w)
    assert(r == Vec3([0, 0, 0])), 'got %s instead' % r
    assert(type(r) == type(v))

    v = Vec3([1, 0, 0])
    w = Vec3([0, 0, 0])
    r = v.cross(w)
    assert(r == Vec3([0, 0, 0])), 'got %s instead' % r
    assert(type(r) == type(v))

    v = Vec3([0, 0, 0])
    w = Vec3([0, 0, 0])
    r = v.cross(w)
    assert(r == Vec3([0, 0, 0])), 'got %s instead' % r
    assert(type(r) == type(v))

    q0 = Quat([1, 2, 3, 5])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([-40, 8, 19, 9])), 'got %s instead' % r
    assert(type(r) == type(q0))

    q0 = Quat([0, 0, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([0, 0, 0, 0])), 'got %s instead' % r
    assert(type(r) == type(q0))

    q0 = Quat([1, 0, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([2, 4, 3, 5])), 'got %s instead' % r
    assert(type(r) == type(q0))

    q0 = Quat([0, 1, 0, 0])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([-4, 2, -5, 3])), 'got %s instead' % r
    assert(type(r) == type(q0))

    q0 = Quat([0, 0, 1, 0])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([-3, 5, 2, -4])), 'got %s instead' % r
    assert(type(r) == type(q0))

    q0 = Quat([0, 0, 0, 1])
    q1 = Quat([2, 4, 3, 5])
    r = q0 * q1
    assert(r == Quat([-5, -3, 4, 2])), 'got %s instead' % r
    assert(type(r) == type(q0))

    q = Quat([2, 4, 3, 5])
    r = q.S()
    assert(r == 2), 'got %s instead' % r
    assert(type(r) == float)
    r = q.V()
    assert (r == Vec3([4, 3, 5])), 'got %s instead' % r
    assert isinstance(r, Vec)

    q = Quat([2, 4, 3, 5])
    r = q.conjugate()
    assert(r == Quat([2, -4, -3, -5])), 'got %s instead' % r
    assert(type(r) == type(q))

    q = Quat([2, 0, 0, 5])
    r = q.conjugate()
    assert(r == Quat([2, 0, 0, -5])), 'got %s instead' % r
    assert(type(r) == type(q))

    q = Quat([0, 0, 0, 0])
    r = q.conjugate()
    assert(r == q), 'got %s instead' % r
    assert(type(r) == type(q))

    r = I * I
    assert(I != E), "This shouldn't hold %s != %s" % (I, E)
    assert(r == E), 'got %s instead' % r

    print 'succes'

