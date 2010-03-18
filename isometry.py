#! /usr/bin/python

import math
import Geom3D
from cgkit import cgtypes
from copy import copy

quat = cgtypes.quat
vec3 = cgtypes.vec3
mat3 = cgtypes.mat3

class Rot(quat):
    def __init__(this, axis, angle):
        quat.__init__(this, angle, vec3(axis))

    def axis(this):
        return this.toAngleAxis()[1]

    def angle(this):
        return this.toAngleAxis()[0]

    def after(this, R):
        return this.toAngleAxis()[0]

    def inverse(this):
        return Rot(this.axis(), -this.angle())

    __minMargin = 1.0e-12
    def __eq__(this, o):
        a0, x0 = this.toAngleAxis()
        a1, x1 = o.toAngleAxis()
        return (
            (
                Geom3D.eq(a0, a1, this.__minMargin)
                and
                Geom3D.Veq(x0, x1, this.__minMargin)
            ) or (
                Geom3D.eq(2*math.pi - a0, a1, this.__minMargin)
                and
                Geom3D.Veq(-x0, x1, this.__minMargin)
            )
        )

    def __ne__(this, o):
        return not this.__eq__(o)

    def __str__(this):
        return 'axis %s angle %f' % (this.axis(), this.angle())

    def __repr__(this):
        return '(%s, %f)' % (this.axis(), this.angle())

    def __mul__(this, o):
        if isinstance(o, Set):
            # try rotation between Rots and Set
            # nodate rmul is important, since the mul is not commutative.
            return o.__rmul__(this)
        #else
        try:
            # try rotation between 2 Rots (or Rot and quat)
            #print 'Rot * rot:', this, '*', o
            a = quat.__mul__(this, o).toAngleAxis()
            #print '  --->', Rot(a[1], a[0])
            return Rot(a[1], a[0])
        except AttributeError:
            raise TypeError, "unsupported op type(s) for *: '%s' and '%s'" % (
                    this.__class__.__name__, o.__class__.__name__
                )

X = [1, 0, 0]
Y = [0, 1, 0]
Z = [0, 0, 1]

hTurn = math.pi         # half turn
qTurn = math.pi/2       # quarter turn
tTurn = 2*math.pi/3     # third turn

acos_1_V3  = math.acos(1.0 / math.sqrt(3))
asin_1_V3  = math.asin(1.0 / math.sqrt(3))
asin_V2_V3 = acos_1_V3
acos_V2_V3 = asin_1_V3

# rotation around x-axis
class Rx(Rot):
    def __init__(this, angle):
        Rot.__init__(this, X, angle)

# rotation around y-axis
class Ry(Rot):
    def __init__(this, angle):
        Rot.__init__(this, Y, angle)

# rotation around z-axis
class Rz(Rot):
    def __init__(this, angle):
        Rot.__init__(this, Z, angle)

# halfturn around x-, y-, and z-axis
Hx = Rx(hTurn)
Hy = Ry(hTurn)
Hz = Rz(hTurn)

# Identity 
E =  Rx(0)

# central inversion
# TODO Hmm now I is no object.. (class)
def I(v):
    return [-x for x in v]

class Set(set):

    def __init__(this, *args):
        set.__init__(this, *args)

    def __eq__(this, o):
        eq = (len(this) == len(o))
        if eq:
            for e in this:
                eq = e in o
                if not eq: break
        return eq

    def __mul__(this, o):
        # print 'isinstance(o, Set)', isinstance(o, Set)
        if isinstance(o, Set):
            # rotation Set(this) * Set(o)
            new = Set([])
            for d in o:
                new.update(this * d)
            return new
        else:
            # rotation Set * Rot
            return Set([e * o for e in this])

    def __rmul__(this, o):
        # Note rotation Set * Set is caught by __mul__
        # rotation Rot * Set
        return Set([o * e for e in this])

    def generateSubgroup(this, o):
        if isinstance(o, quat):
            # generate the quotient set THIS / o
            assert o in this, "Generator of sub-group should be part of group"
            subgroup = Set([o])
            subgroup.group()
            return subgroup
        else:
            for e in o:
                assert e in this, "sub-group should be part of group"
            subgroup = copy(o)
            subgroup.group()
            return subgroup

    def __div__(this, o):
        # this * subgroup: right quotient set
        # make sure o is a subgroup:
        subgroup = this.generateSubgroup(o)
        q = [] # initialise quotient set.
        for e in this:
            s = e * o
            if s not in q: q.append(s)
        return q

    def __rdiv__(this, o):
        #  subgroup * this: left quotient set
        pass # TODO

    def __contains__(this, o):
        # Needed for 'in' relationship: default doesn't work, it seems to
        # compare the elements id.
        #print this.__class__.__name__, '__contains__'
        for e in this:
            if e == o:
                return True
        return False

    def add(this, e):
        if e not in this:
            set.add(this, e)

    def update(this, o):
        for e in o:
            this.add(e)

    def __str__(this):
        s = '%s = {' % this.__class__.__name__
        for d in this:
            s = '%s\n  %s,' % (s, str(d))
        s = '%s\n}' % s
        # TODO if there is an opposite isometry...
        return s

    def group(this, maxIter = 50):
        """
        Tries to make a group out of the set of isometries

        If it succeeds within maxiter step this set is closed, contains the unit
        element and the set contains for every elements its inverse
        """
        result = copy(this)
        for e in this:
            result.add(e.inverse())
        result.add(E)
        this.clear()
        this.update(result.closed(maxIter))

    def closed(this, maxIter = 50):
        """
        Return a set that is closed, if it can be generated within maxIter steps.
        """
        result = copy(this)
        for i in range(maxIter):
            lPrev = len(result)
            # print 'close step', i, 'len:', lPrev
            result.update(result * result)
            l = len(result)
            if l == lPrev:
                break
            # print '  --> new group with len', l, ':\n', result
        assert (l == lPrev), "couldn't close group after %d iterations"% maxIter
        return result

    def close(this, maxIter = 50):
        """
        Closes the current set, if it can be done within maxIter steps.
        """
        result = this.closed(maxIter)
        this.clear()
        this.update(result)

class Identity(Set):
    initPars = []
    order    = 1
    def __init__(this, isometries = None, setup = {}):
        Set.__init__(this, [E])

C1 = Identity

class Cn(Set):
    initPars = [
        {'type': 'int', 'par': 'n',    'lab': "order"},
        {'type': 'vec3', 'par': 'axis', 'lab': "n-fold axis"}
    ]
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group Cn, consisting of n rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        """
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(this, isometries)
        else:
            keys = setup.keys()
            if 'axis' in keys: axis = setup['axis']
            else:              axis = Z[:]
            if 'n' in keys: n = setup['n']
            else:           n = 2
            if n == 0: n = 1

            angle = 2 * math.pi / n
            try:   r = Rot(axis, angle)
            except TypeError: r = Rot(axis.toAngleAxis()[1], angle)

            isometries = [r]
            for i in range(n-1):
                isometries.append(r * isometries[-1])
            Set.__init__(this, isometries)

class A4(Set):
    initPars = [
        {'type': 'vec3', 'par': 'o2axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o2axis1', 'lab': "half turn of orthogonal axis"}
    ]
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group A4, consisting of 12 rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - the identity E, and 3 orthogonal halfturns
        - 4 order 3 isometries.
        The group can be generated by 2 half turns, but this will not generate
        the group uniquely: There are 2 possibilities: the two tetrahedra in a
        Stella Octagula. If this setup doesn't matter just specify the
        axes of 2 half turns. Otherwise one should specify the order 3 axis
        as well.
        """
        # A4 consists of:
        # 1. A subgroup D2: E, and half turns H0, H1, H2
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            assert len(isometries) == 12, "12 != %d" % (len(isometries))
            # TODO: more asserts?
            Set.__init__(this, isometries)
        else:
            axes = setup.keys()
            if 'o2axis0' in axes: o2axis0 = setup['o2axis0']
            else:                 o2axis0 = X[:]
            if 'o2axis1' in axes: o2axis1 = setup['o2axis1']
            else:                 o2axis1 = Y[:]
            assert vec3(o2axis0) * vec3(o2axis1) == 0, "Error: axes not orthogonal"
            try:   H0 = Rot(o2axis0, hTurn)
            except TypeError: H0 = Rot(o2axis0.toAngleAxis()[1], hTurn)
            try:   H1 = Rot(o2axis1, hTurn)
            except TypeError: H1 = Rot(o2axis1.toAngleAxis()[1], hTurn)
            H2 = H1 * H0

            # the one order 3 rotation axis, is obtained as follows:
            # imagine A4 is part of S4 positioned in a cube
            # H0, H1, H2 go through the cube face centres
            # define a quarter turn around H2
            Q = Rot(H2.axis(), qTurn)
            # h0 and h1 go through cube edge centres
            h0 = Q * H0
            h1 = Q * H1
            # o3axis goes through 1 of the 2 cube vertices that form the edge
            # between the faces which centres are on H0 and H1 
            o3axis = Rot(h0.axis(), asin_1_V3).toMat4() * h1.axis()

            # R0_1_3: 1/3 rotation around the first order 3 axis
            # R0_2_3: 2/3 rotation around the first order 3 axis
            R1_1_3 = Rot(o3axis, tTurn)
            R1_2_3 = Rot(o3axis, 2*tTurn)
            R4_1_3 = R1_1_3 * H0
            R3_1_3 = R1_1_3 * H1
            R2_1_3 = R1_1_3 * H2
            # TODO: check if this is correct for all possible o3
            R2_2_3 = R1_2_3 * H0
            R4_2_3 = R1_2_3 * H1
            R3_2_3 = R1_2_3 * H2
            # print 'E', E
            # print 'H0', H0
            # print 'H1', H1
            # print 'H2', H2
            # print 'R1_1_3', R1_1_3
            # print 'R1_2_3', R1_2_3
            # print 'R2_1_3', R2_1_3
            # print 'R2_2_3', R2_2_3
            # print 'R3_1_3', R3_1_3
            # print 'R3_2_3', R3_2_3
            # print 'R4_1_3', R4_1_3
            # print 'R5_2_3', R4_2_3
            Set.__init__(this, [
                    E, H0, H1, H2,
                    R1_1_3, R1_2_3,
                    R2_1_3, R2_2_3,
                    R3_1_3, R3_2_3,
                    R4_1_3, R4_2_3
                ])

if __name__ == '__main__':
    r = Rot([1, 1, 1], 30)
    print 'print(Rot([1, 1, 1], 30))', r
    print 'repr(Rot([1, 1, 1], 30))', repr(r)

    g = Set([Hx, Hy])
    print 'Initialised set g:', g
    print 'Rot([1, 0, 0], hTurn) in g:',  Rot([1, 0, 0], hTurn) in g
    print 'Rot([-1, 0, 0], -hTurn) in g:',  Rot([-1, 0, 0], -hTurn) in g
    print 'Set g after closing:'
    g.close()
    print g

    g = Set([Rot(X, qTurn)])
    print 'Initialised set g:', g
    print 'Rot([1, 0, 0], qTurn) in g:',  Rot(X, qTurn) in g
    print 'Rot([-1, 0, 0], -qTurn) in g:',  Rot(-vec3(X), -qTurn) in g
    print 'Set g after closing:'
    g.close()
    print g

    a4 = A4(o2axis0 = [1, 1, 1], o2axis1 = [1, -1, 0])
    print 'A4(o2axis0 = [1, 1, 1], o2axis1 = [1, -1, 0])'
    print a4
    ca4 = copy(a4)
    a4.group()
    print 'making a group out of this, should not change the result:'
    print a4 == ca4

    a4 = A4(o2axis0 = X, o2axis1 = Y)
    print a4


    ########################################################################
    # Quotient Set:
    print 'group a4:'
    a4 = A4(o2axis0 = X, o2axis1= Y)
    print a4
    print 'has a subgroup D2:'
    D2 = Set([Hx, Hy])
    D2.group()
    print D2
    print 'which defines a right quotient set s = ['
    q = a4 / D2
    for s in q: print s
    print ']'

    # TODO: the result is wrong: you need to multiply all axes, but you need to
    # keep the angle. However, above you use the multiplucation already to close
    # the group.
#    print 'Rot(X, qTurn) * a4:\n', a4 * Rot(X, qTurn)
    # Note the when printing R4_1_3 it might be expressed as a rotation around
    # the axis in the opposite direction around - alpha...

