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
        try:
            r = len(v) == len(w)
        except TypeError:
            print 'info: comparing different types in Vec (%s)' % v.__class__.__name__
            return False
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

ux = Vec3([1, 0, 0])
uy = Vec3([0, 1, 0])
uz = Vec3([0, 0, 1])

class Quat(Vec):
    def __init__(this, v = None):
        # if 3D vector, use it to set vector part only and use 0 for scalar part
        if len(v) == 3: v.insert(0, 0)
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

class Transform3():
    def __init__(this, qLeft, qRight):
        this.left = qLeft
        this.right = qRight

    def __repr__(v):
        return '%s(%s, %s)' % (v.__class__.__name__, v.left, v.right)

    def __str__(v):
        return '%s * .. * %s' % (v.left, v.right)

    def __mul__(v, w):
        if isinstance(w, Transform3):
            # v * w =  vLeft * wLeft .. wRight * vRight
            return Transform3(v.left * w.left, w.right * v.right)
        elif isinstance(w, Vec) and len(w) == 3:
            # TODO: check kind of Transform3
            return (v.left * Quat([0, w[0], w[1], w[2]]) * v.right).V()
        elif isinstance(w, Quat):
            return (v.left * w                           * v.right).V()
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
        return (
            -v.right.conjugate() == v.left
            and
            v.right.N() == 1
        )

    isRotRefl = isRotInv

class Rot3(Transform3):
    def __init__(this, v = None, axis = Vec3([1, 0, 0]), angle = 0):
        """
        Initialise a 3D rotation
        """
        if v != None:
            v = v.N()
            Transform3.__init__(this, v, v.conjugate())
        else:
            # v = cos(angle) + y sin(angle)
            alpha = angle / 2
            if axis != Vec3([0, 0, 0]):
                axis = axis.N()
            v = math.sin(alpha) * axis
            v = Quat([math.cos(alpha), v[0], v[1], v[2]])
            #print 'cos =', math.cos(alpha)
            #print 'sin =', math.sin(alpha)
            Transform3.__init__(this, v, v.conjugate())

    def __str__(v):
        return 'Rotation of %s rad around %s' % (v.angle(), v.axis())

    def angle(v):
            cos = v.left[0]
            sin = v.left[1] / v.left.V().N()[0]
            #print 'reconstructed cos =', cos
            #print 'reconstructed sin =', sin
            return 2 * math.atan2(sin, cos)

    def axis(v):
            return v.left.V().N()

class HalfTurn3(Rot3):
    def __init__(this, axis):
        Rot3.__init__(this, axis = axis, angle = math.pi)

class Refl3(Transform3):
    def __init__(this, q = None, normal = None):
        Transform3.__init__(this, v)

class RotInv3(Transform3):
    def __init__(this, q = None, axis = None, angle = None):
        try:
            qLeft = -q.conjugate()
        except AttributeError:
            # in case q is a Vec
            q = Quat(q)
            qLeft = -q.conjugate()
        Transform3.__init__(this, qLeft, q)

    def __str__(q):
        return '%s * .. * %s' % (q.left, q.right)

    def __repr__(q):
        return '%s(%s, %s)' % (q.__class__.__name__, q.left, q.right)

RotRefl = RotInv3
I = RotInv3(Quat([1, 0, 0, 0]))
E = Rot3(Quat([1, 0, 0, 0]))

# TODO implement Geom3D.Line3D here (in this file)

if __name__ == '__main__':

    # Vec
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

    # Vec3
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

    # Quat
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

    # Transform
    assert I.__repr__() == 'RotInv3([-1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0])'

    r = I * I
    assert(I != E), "This shouldn't hold %s != %s" % (I, E)
    assert(r == E), 'got %s instead' % r

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
    assert(r == ux), 'got %s instead' % r

    q = Rot3(axis = uz, angle = 2*math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == ux), 'got %s instead' % r

    q = Rot3(axis = uz, angle = -2*math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == ux), 'got %s instead' % r

    # 90 degrees (+/- 360)
    q = Rot3(axis = uz, angle = math.pi/2)
    v = Vec3(ux)
    r = q*v
    assert(r == uy), 'got %s instead' % r

    q = Rot3(axis = uz, angle = math.pi/2 + 2 * math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == uy), 'got %s instead' % r

    q = Rot3(axis = uz, angle = math.pi/2 - 2 * math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == uy), 'got %s instead' % r

    # 180 degrees (+/- 360)
    q = Rot3(axis = uz, angle = math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == -ux), 'got %s instead' % r

    q = Rot3(axis = uz, angle = math.pi + 2 * math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == -ux), 'got %s instead' % r

    q = Rot3(axis = uz, angle = math.pi - 2 * math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == -ux), 'got %s instead' % r

    # -90 degrees (+/- 360)
    q = Rot3(axis = uz, angle = -math.pi/2)
    v = Vec3(ux)
    r = q*v
    assert(r == -uy), 'got %s instead' % r

    q = Rot3(axis = uz, angle = -math.pi/2 + 2 * math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == -uy), 'got %s instead' % r

    q = Rot3(axis = uz, angle = -math.pi/2 - 2 * math.pi)
    v = Vec3(ux)
    r = q*v
    assert(r == -uy), 'got %s instead' % r

    # Quadrant I
    hV3 = math.sqrt(3) / 2
    q = Rot3(axis = uz, angle = math.pi/3)
    v = Vec3(ux)
    v[2] = 3
    r = q*v
    assert(r == Vec3([0.5, hV3, 3])), 'got %s instead' % r

    # Quadrant II
    q = Rot3(axis = uz, angle = math.pi - math.pi/3)
    v = Vec3(ux)
    v[2] = 3
    r = q*v
    assert(r == Vec3([-0.5, hV3, 3])), 'got %s instead' % r

    # Quadrant III
    q = Rot3(axis = uz, angle = math.pi + math.pi/3)
    v = Vec3(ux)
    v[2] = 3
    r = q*v
    assert(r == Vec3([-0.5, -hV3, 3])), 'got %s instead' % r

    # Quadrant IV
    q = Rot3(axis = uz, angle = - math.pi/3)
    v = Vec3(ux)
    v[2] = 3
    r = q*v
    assert(r == Vec3([0.5, -hV3, 3])), 'got %s instead' % r

    # 3D Quadrant I: rotation around (1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([1, 1, 1]), angle = 2 * math.pi/3)
    v = Vec3([-1, 1, 1])
    r = q*v
    assert(r == Vec3([1, -1, 1])), 'got %s instead' % r
    # neg angle
    q = Rot3(axis = Vec3([1, 1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, 1, -1])), 'got %s instead' % r
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([1, 1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, -1, 1])), 'got %s instead' % r
    # neg axis
    q = Rot3(axis = -Vec3([1, 1, 1]), angle = 2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, 1, -1])), 'got %s instead' % r

    # 3D Quadrant II: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([-1, 1, 1]), angle = 2 * math.pi/3)
    v = Vec3([1, 1, 1])
    r = q*v
    assert(r == Vec3([-1, 1, -1])), 'got %s instead' % r
    # neg angle
    q = Rot3(axis = Vec3([-1, 1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % r
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([-1, 1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([-1, 1, -1])), 'got %s instead' % r
    # neg axis
    q = Rot3(axis = -Vec3([-1, 1, 1]), angle = 2 * math.pi/3)
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % r

    # 3D Quadrant III: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([-1, -1, 1]), angle = 2 * math.pi/3)
    v = Vec3([1, 1, 1])
    r = q*v
    assert(r == Vec3([-1, 1, -1])), 'got %s instead' % r
    # neg angle
    q = Rot3(axis = Vec3([-1, -1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % r
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([-1, -1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([-1, 1, -1])), 'got %s instead' % r
    # neg axis
    q = Rot3(axis = -Vec3([-1, -1, 1]), angle = 2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % r

    # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([1, -1, 1]), angle = 2 * math.pi/3)
    v = Vec3([1, 1, 1])
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % r
    # neg angle
    q = Rot3(axis = Vec3([1, -1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % r
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([1, -1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % r
    # neg axis
    q = Rot3(axis = -Vec3([1, -1, 1]), angle = 2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % r

    # test quat mul from above (instead of Vec3):
    # 3D Quadrant IV: rotation around (-1, 1, 1): don't specify normalise axis
    q = Rot3(axis = Vec3([1, -1, 1]), angle = 2 * math.pi/3)
    v = Quat([0, 1, 1, 1])
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % r
    # neg angle
    q = Rot3(axis = Vec3([1, -1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % r
    # neg axis, neg angle
    q = Rot3(axis = -Vec3([1, -1, 1]), angle = -2 * math.pi/3)
    r = q*v
    assert(r == Vec3([-1, -1, 1])), 'got %s instead' % r
    # neg axis
    q = Rot3(axis = -Vec3([1, -1, 1]), angle = 2 * math.pi/3)
    r = q*v
    assert(r == Vec3([1, -1, -1])), 'got %s instead' % r

    # Axis Angle:
    v = Vec3([1, -1, 1])
    a = 2 * math.pi/3
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
    # neg angle
    v = Vec3([1, -1, 1])
    a = -2 * math.pi/3
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
    # neg angle, neg axis
    v = Vec3([-1, 1, -1])
    a = -2 * math.pi/3
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
    # neg axis
    v = Vec3([-1, 1, -1])
    a = 2 * math.pi/3
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

    print 'succes'

