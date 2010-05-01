#! /usr/bin/python

import math
import re
import GeomTypes
from copy import copy

X = GeomTypes.ux
Y = GeomTypes.uy
Z = GeomTypes.uz

hTurn = math.pi         # half turn
qTurn = math.pi/2       # quarter turn
eTurn = qTurn/2         # one eighth turn
tTurn = 2*math.pi/3     # third turn

acos_1_V3  = math.acos(1.0 / math.sqrt(3))
asin_1_V3  = math.asin(1.0 / math.sqrt(3))
asin_V2_V3 = acos_1_V3
acos_V2_V3 = asin_1_V3

# halfturn around x-, y-, and z-axis
Hx = GeomTypes.Hx
Hy = GeomTypes.Hy
Hz = GeomTypes.Hz

I  = GeomTypes.I       # central inversion

class ImproperSubgroupError(ValueError):
    "Raised when subgroup is not really a subgroup"

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

    def __sub__(this, o):
        new = Set([])
        for e in this:
            if e not in o:
                set.add(new, e)
        return new

    def __or__(this, o):
        new = Set(this)
        for e in o:
            new.add(e)
        return new

    def __mul__(this, o):
        if isinstance(o, Set):
            # Set(this) * Set(o)
            new = Set([])
            for d in o:
                new.update(this * d)
            return new
        else:
            # Set * GeomTypes.Transform3
            return Set([e * o for e in this])

    def __rmul__(this, o):
        # Note rotation Set * Set is caught by __mul__
        # rotation Rot * Set
        return Set([o * e for e in this])

    def isGroup(this):
        if len(this) == 0: return False
        isGroup = True
        for e in this:
            # optimised away, done as part of next loop:
            # if not (e.inverse() in this):
            thisHasInverse = False
            for o in this:
                thisHasInverse  = thisHasInverse | (e.inverse() == o)
                isClosedForThis = e*o in this and o*e in this
                if not isClosedForThis:
                    break;
            if not thisHasInverse or not isClosedForThis:
                isGroup = False
                break;

        return isGroup
        # the following is not needed to check, is done implicitly:
        # and (GeomTypes.E in this)

    def isSubgroup(this, o):
        """returns whether this is a subgroup of o)"""
        if len(this) > len(o): return False # optimisation
        return this.isGroup() and this.issubset(o)

    def subgroup(this, o):
        try:
            if isinstance(o, GeomTypes.Transform3):
                # generate the quotient set THIS / o
                assert o in this
                subgroup = Set([o])
                subgroup.group()
                return subgroup
            else:
                # o is already a set
                #print 'subgroup: this:', this
                #print 'subgroup: o:', o
                for e in o:
                    assert e in this, '%s not in %s' % (e,
                        this.__class__.__name__)
                subgroup = copy(o)
                # for optimisation: don't call group (slow) for this == o:
                if len(subgroup) < len(this):
                    subgroup.group()
                elif len(subgroup) > len(this):
                    raise ImproperSubgroupError, '%s not <= %s (with this orientation)' % (
                        o.__class__.__name__, this.__class__.__name__)
                return subgroup
        #except ImproperSubgroupError:
        except AssertionError:
            raise ImproperSubgroupError, '%s not <= %s (with this orientation)' % (
                o.__class__.__name__, this.__class__.__name__)

    def __div__(this, o):
        # this * subgroup: right quotient set
        # make sure o is a subgroup:
        if (len(o) > len(this)): return o.__div__(this)
        o = this.subgroup(o)
        assert len(o) <= len(this)
        # use a list of sets, since sets are unhashable
        quotientSet = []
        # use a big set for all elems found so for
        foundSoFar = Set([])
        for te in this:
            q = te * o
            if q.getOne() not in foundSoFar:
                quotientSet.append(q)
                foundSoFar = foundSoFar.union(q)
        return quotientSet

    quotientSet = __div__

    def __rdiv__(this, o):
        #  subgroup * this: left quotient set
        pass # TODO

    def __contains__(this, o):
        # Needed for 'in' relationship: default doesn't work, it seems to
        # compare the elements id.
        #print this.__class__.__name__, '__contains__'
        for e in this:
            if e == o:
                #print 'e == o'
                #print '  - with e:', e
                #print '           ', e.__repr__()
                #print '  - with o:', o
                #print '           ', o.__repr__()
                return True
        return False

    def add(this, e):
        l = len(this)
        if e not in this:
            set.add(this, e)

    def update(this, o):
        for e in o:
            this.add(e)

    def getOne(this):
        for e in this: return e

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
        result.add(GeomTypes.E)
        this.clear()
        this.update(result.close(maxIter))

    def close(this, maxIter = 5):
        """
        Return a set that is closed, if it can be generated within maxIter steps.
        """
        result = copy(this)
        for i in range(maxIter):
            lPrev = len(result)
            #print 'close step', i, 'len:', lPrev
            result.update(result * result)
            l = len(result)
            if l == lPrev:
                break
            # print '  --> new group with len', l, ':\n', result
        #if not l == lPrev:
        #    for i in this: print i
        #    print '---------------'
        #    for i in result: print i
        assert (l == lPrev), "couldn't close group after %d iterations"% maxIter
        return result

def setup(**kwargs): return kwargs

class E(Set):
    initPars = []
    order = 1
    def __init__(this, isometries = None, setup = {}):
            Set.__init__(this, [GeomTypes.E])

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        return [E()]

C1 = E

class ExI(Set):
    initPars = []
    order = 2
    def __init__(this, isometries = None, setup = {}):
            Set.__init__(this, [GeomTypes.E, GeomTypes.I])

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == ExI:
            return [this]
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

C1xI = ExI

class Cn(Set):
    initPars = [
        {'type': 'int', 'par': 'n',    'lab': "order"},
        {'type': 'vec3', 'par': 'axis', 'lab': "n-fold axis"}
    ]
    order = 0
    n = 0
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
            if this.n != 0   : n = this.n
            else:
                if 'n' in keys: n = setup['n']
                else:           n = 2
                if n == 0: n = 1
                this.n = n

            angle = 2 * math.pi / n
            try:   r = GeomTypes.Rot3(axis = axis, angle = angle)
            except TypeError:
                # assume axis has Rot3 type
                r = GeomTypes.Rot3(axis = axis.axis(), angle = angle)

            isometries = [r]
            for i in range(n-1):
                isometries.append(r * isometries[-1])
            Set.__init__(this, isometries)
            this.order = n
            this.rotAxes = {'n': axis}

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        sgName = sg.__name__
        if sg == Cn:
            if sg.order == this.order:
                return [this]
            elif sg.order > this.order:
                return []
            else:
                assert False, 'TODO'
                return [E()]
        elif sgName[0] == 'C':
            try: # Cn
                n = int(sgName[1:])
                if n == this.order:
                    return [this]
                elif n > this.order:
                    return []
                else:
                    assert False, 'TODO'
                    return [E()]
            except ValueError: # caused by int() function, eg for CnxI
                raise ImproperSubgroupError, '%s ! <= %s' % (
                        this.__class__.__name__, sg.__class__.__name__)
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

# dynamically create Cn classes:
class MetaCn(type):
    def __init__(this, classname, bases, classdict):
        type.__init__(this, classname, bases, classdict)
def C(n):
    if n == 1: return E
    C_n = MetaCn('C%d' % n, (Cn,),
            {
                'n'    : n,
                'order': n,
                'initPars': [{
                        'type': 'vec3',
                        'par': 'axis',
                        'lab': "%d-fold axis" % n
                    }]
            }
        )
    # TODO: fix subgroups depending on n:
    C_n.subgroups = [C_n, E]
    return C_n

C2 = C(2)
C3 = C(3)
C4 = C(4)

reC2nCn = re.compile('C([0-9]+)C([0-9]+)$')
class C2nCn(Cn):
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group C2nCn, consisting of n rotations and of n rotary
        inversions (reflections)

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n rotary inversions around one n-fold axis (angle: pi(1 + 2i)/n, with 
          0 <= i < n)
        """
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(this, isometries)
        else:
            s = copy(setup)
            if 'n' not in s and this.n != 0:
                s['n'] = this.n
            cn = Cn(setup = s)
            this.n = cn.n
            s['n'] = 2 * s['n']
            c2n = Cn(setup = s)
            Set.__init__(this, cn | ((c2n-cn) * GeomTypes.I))
            this.rotAxes = {'n': cn.rotAxes['n']}
            this.order = c2n.order

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        sgName = sg.__name__
        if sg == C2nCn:
            if sg.order == this.order:
                return [this]
            elif sg.order > this.order:
                return []
            else:
                assert False, 'TODO'
                return [E()]
        elif sgName[0] == 'C': # Cn
            m = reC2nCn.match(sgName)
            if m:
                n2 = int(m.group(1))
                n  = int(m.group(2))
                if not n2 == 2 * n: return []
                order = sg.order
                if order == this.order:
                    return [this]
                elif order > this.order:
                    return []
                elif order == 2: # {E, Reflection}
                    assert (this.order / 2) % 2 == 1, 'Improper subgroup'
                    # only one orientation: reflection normal parallel to
                    # n-fold axis.
                    return [sg(setup = {'axis': this.rotAxes['n']})]
                else:
                    assert False, 'TODO: %s (order %d)' % (sgName, order)
                    return [E()]
            else:
                try:
                    n = int(sgName[1:])
                    if 2 * n == this.order:
                        # only one orientation:
                        return [sg(setup = {'axis': this.rotAxes['n']})]
                    else:
                        assert False, 'TODO'
                except ValueError: # caused by int() function
                    assert False, 'TODO'
                    pass #TODO
                    # try C2nxCn

        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

# dynamically create CnxI classes:
class MetaC2nCn(type):
    def __init__(this, classname, bases, classdict):
        type.__init__(this, classname, bases, classdict)
def C2nC(n):
    C_2n_C_n = MetaC2nCn('C%dC%d' % (2*n, n), (C2nCn,),
            {
                'n'    : n,
                'order': 2 * n,
                'initPars': [{
                        'type': 'vec3',
                        'par': 'axis',
                        'lab': "%d-fold axis" % n
                    }]
            }
        )
    C_2n_C_n.subgroups = [C_2n_C_n, C(n), E]
    # Add subgroup {E, reflection}
    if n % 2 == 1:
        if n != 1:
            C_2n_C_n.subgroups.insert(-1, C2C1)
    # TODO: fix more subgroups depending on n, e.g.:
    #else:
    #    if n != 2:
    #        C_2n_C_n.subgroups.insert(-2, C2nC(2))
    return C_2n_C_n

C2C1 = C2nC(1)
C4C2 = C2nC(2)
C6C3 = C2nC(3)
C8C4 = C2nC(4)

class CnxI(Cn):
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group CnxI, consisting of n rotations and of n rotary
        inversions (reflections)

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n rotary inversions around one n-fold axis (angle: i * 2pi/n, with 
          0 <= i < n)
        """
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(this, isometries)
        else:
            s = copy(setup)
            if 'n' not in s and this.n != 0:
                s['n'] = this.n
            cn = Cn(setup = s)
            this.n = cn.n
            Set.__init__(this, cn * ExI())
            this.rotAxes = {'n': cn.rotAxes['n']}
            this.order = 2 * cn.order

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        sgName = sg.__name__
        if sg == CnxI:
            if sg.order == this.order:
                return [this]
            elif sg.order > this.order:
                return []
            else:
                assert False, 'TODO'
                return [E()]
        elif sgName[0] == 'C':
            if sgName[-2:] == 'xI': # CnxI
                try:
                    n = int(sgName[1:-2])
                    order = sg.order
                    if order == this.order:
                        return [this]
                    elif order > this.order:
                        return []
                    else:
                        assert False, 'TODO: %s (order %d)' % (sgName, order)
                        return [E()]
                except ValueError: # caused by int() function
                    raise ImproperSubgroupError, '%s ! <= %s' % (
                        this.__class__.__name__, sg.__class__.__name__)
            else: # Cn
                m = reC2nCn.match(sgName)
                if m:
                    n2 = int(m.group(1))
                    n  = int(m.group(2))
                    if not n2 == 2 * n: return []
                    if n2 ==2 and n == 1:
                        return [sg(setup = {'axis': this.rotAxes['n']})]
                else:
                    try:
                        n = int(sgName[1:])
                        if 2 * n == this.order:
                            # only one orientation:
                            return [sg(setup = {'axis': this.rotAxes['n']})]
                        else:
                            assert False, 'TODO'
                    except ValueError: # caused by int() function
                        assert False, 'TODO'
                        pass #TODO
                        # try C2nxCn

        elif sg == ExI:
            return [ExI()]
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

# dynamically create CnxI classes:
class MetaCnxI(type):
    def __init__(this, classname, bases, classdict):
        type.__init__(this, classname, bases, classdict)
def CxI(n):
    if n == 1: return ExI
    C_nxI = MetaCnxI('C%dxI' % n, (CnxI,),
            {
                'n'    : n,
                'order': 2 * n,
                'initPars': [{
                        'type': 'vec3',
                        'par': 'axis',
                        'lab': "%d-fold axis" % n
                    }]
            }
        )
    # TODO: fix subgroups depending on n:
    C_nxI.subgroups = [C_nxI, C(n), C1xI, E]
    # Add subgroup {E, reflection}
    if n % 2 == 0:
        if n != 0:
            C_nxI.subgroups.insert(-2, C2C1)
    return C_nxI

C1xI = CxI(1)
C2xI = CxI(2)
C3xI = CxI(3)
C4xI = CxI(4)

reDnCn = re.compile('D([0-9]+)C([0-9]+)$')
class DnCn(Cn):
    initPars = [
        {'type': 'int',  'par': 'n',    'lab': "order"},
        {'type': 'vec3', 'par': 'axis_n', 'lab': "n-fold axis"},
        {'type': 'vec3', 'par': 'normal_r', 'lab': "normal of reflection"}
    ]
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group DnCn, consisting of n rotations and of n rotary
        inversions (reflections)

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n reflections in planes that share the n-fold axis.
        """
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(this, isometries)
        else:
            s = {}
            if 'n' not in setup:
                if this.n != 0:
                    s['n'] = this.n
            else:
                s['n'] = setup['n']
            if 'axis_n' in setup:
                s['axis_n'] = setup['axis_n']
            cn = Cn(setup = s)
            this.n = cn.n
            if 'normal_r' in setup:
                s['axis_2'] = setup['normal_r']
            dn = Dn(setup = s)
            Set.__init__(this, cn | ((dn-cn) * GeomTypes.I))
            this.n = s['n']
            this.rotAxes = {'n': cn.rotAxes['n']}
            this.reflNormals = dn.rotAxes[2]
            this.order = dn.order

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        sgName = sg.__name__
        if sg == DnCn:
            if sg.order == this.order:
                return [this]
            elif sg.order > this.order:
                return []
            else:
                assert False, 'TODO'
                return [E()]
        elif isinstance(sg, MetaCn):
            if sg.n == this.n:
                return [sg(setup = {'axis': this.rotAxes['n']})]
            else:
                TODO
        elif isinstance(sg, MetaC2nCn):
            if sg.n == 1: # C2C1
                return [sg(setup = {'axis': rn}) for rn in this.reflNormals]
            else:
                TODO
        elif isinstance(sg, MetaDnCn):
            if sg.n == this.n:
                return [this]
            else:
                TODO
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

# dynamically create DnCn classes:
class MetaDnCn(type):
    def __init__(this, classname, bases, classdict):
        type.__init__(this, classname, bases, classdict)

def DnC(n):
    if n == 1: return C2C1
    D_n_C_n = MetaDnCn('D%dC%d' % (n, n), (DnCn,),
            {
                'n'    : n,
                'order': 2 * n,
                'initPars': [{
                        'type': 'vec3',
                        'par': 'axis',
                        'lab': "%d-fold axis" % n
                    }, {
                        'type': 'vec3',
                        'par': 'normal_r',
                        'lab': "normal of reflection"
                    }]
            }
        )
    D_n_C_n.subgroups = [D_n_C_n, C(n), C2C1, E]
    # TODO: fix more subgroups depending on n, e.g.:
    return D_n_C_n

D1C1 = DnC(1)
D2C2 = DnC(2)
D3C3 = DnC(3)
D4C4 = DnC(4)

class Dn(Set):
    initPars = [
        {'type': 'int',  'par': 'n',    'lab': "order"},
        {'type': 'vec3', 'par': 'axis_n', 'lab': "n-fold axis"},
        {'type': 'vec3', 'par': 'axis_2', 'lab': "axis of halfturn"}
    ]
    order = 0
    n = 0
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group Dn, consisting of 2n rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n halfturns around axes perpendicular to the n-fold axis
        """
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(this, isometries)
        else:
            keys = setup.keys()
            if 'axis_n' in keys: axis_n = setup['axis_n']
            else:                axis_n = Z[:]
            if 'axis_2' in keys: axis_2 = setup['axis_2']
            else:                axis_2 = X[:]
            if this.n != 0     : n = n
            else:
                if 'n' in keys: n = setup['n']
                else:           n = 2
                if n == 0: n = 1

            h = GeomTypes.HalfTurn3(axis_2)
            cn = Cn(setup = {'axis': axis_n, 'n': n})
            isometries = [isom for isom in cn]
            hs = [isom * h for isom in cn]
            #for isom in hs: print isom
            isometries.extend(hs)
            this.rotAxes = {'n': axis_n, 2: [h.axis() for h in hs]}
            Set.__init__(this, isometries)
            this.n     = n
            this.order = 2 * n

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        sgName = sg.__name__
        if sg == Dn:
            if sg.order == this.order:
                return [this]
            elif sg.order > this.order:
                return []
            else:
                assert False, 'TODO'
                return [E()]
        elif sgName[0] == 'D':
            try: # Dn
                n = int(sgName[1:])
                if 2*n == this.order:
                    return [this]
                elif 2*n > this.order:
                    return []
                else:
                    assert False, 'TODO'
                    return [E()]
            except ValueError: # caused by int() function, eg for DnxI
                raise ImproperSubgroupError, '%s ! <= %s' % (
                        this.__class__.__name__, sg.__class__.__name__)
        elif sgName[0] == 'C':
            try: # Cn
                n = int(sgName[1:])
                assert n > 1, 'warning'
                if n == 2: # sg = C2
                    isoms = [
                        C2(setup = {'axis':this.rotAxes[2][i]})
                        for i in range(len(this.rotAxes[2]))
                    ]
                    if this.order % 4 == 0: # if D2, D4, etc
                        isoms.append(
                            Cn(setup = {'n': n, 'axis': this.rotAxes['n']})
                        )
                    return isoms
                elif 2*n == this.order:
                    return [Cn(setup = {'n': n, 'axis': this.rotAxes['n']})]
                elif 2*n > this.order:
                    return []
                else:
                    assert False, 'TODO'
                    return [E()]
            except ValueError: # caused by int() function, eg for CnxI
                raise ImproperSubgroupError, '%s ! <= %s' % (
                        this.__class__.__name__, sg.__class__.__name__)
        elif sg == E:
            return [E()]

# dynamically create Dn classes:
class MetaDn(type):
    def __init__(this, classname, bases, classdict):
        type.__init__(this, classname, bases, classdict)
def D(n):
    if n == 1: return C2
    D_n = MetaDn('D%d' % n, (Dn,),
            {
                'n'    : n,
                'order': 2 * n,
                'initPars': [
                        {
                            'type': 'vec3',
                            'par': 'axis_n',
                            'lab': "%d-fold axis" % n
                        }, {
                            'type': 'vec3',
                            'par': 'axis_2',
                            'lab': "axis of halfturn"
                        }
                    ]
            }
        )
    # TODO: fix subgroups depending on n:
    D_n.subgroups = [D_n, C2, E]
    if n != 2:
        D_n.subgroups.insert(-1, C(n))
    return D_n

D2 = D(2)
D3 = D(3)
D4 = D(4)

class DnxI(Dn):
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group DnxI, of order 4n.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n halfturns around axes perpendicular to the n-fold axis
        - n rotary inversions around one n-fold axis (angle: i * 2pi/n, with
          0 <= i < n). For n even these become n reflections in a plane
          perpendicular to the n-fold axis.
        - n reflections in planes that contain the n-fold axis
        """
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(this, isometries)
        else:
            s = copy(setup)
            if 'n' not in s and this.n != 0:
                s['n'] = this.n
            dn = Dn(setup = s)
            Set.__init__(this, dn * ExI())
            this.rotAxes = {'n': dn.rotAxes['n'], 2: dn.rotAxes[2][:]}
            this.n     = dn.n
            this.order = 2 * dn.order

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        sgName = sg.__name__
        #print 'realiseSubgroups', sgName
        if sg == DnxI:
            if sg.order == this.order:
                return [this]
            elif sg.order > this.order:
                return []
            else:
                assert False, 'TODO'
                return [E()]
        elif sgName[0] == 'D':
            if sgName[-2:] == 'xI': # DnxI
                try:
                    n = int(sgName[1:-2])
                    order = sg.order
                    if order == this.order:
                        return [this]
                    elif order > this.order:
                        return []
                    else:
                        assert False, 'TODO: %s (order %d)' % (sgName, order)
                        return [E()]
                except ValueError: # caused by int() function
                    raise ImproperSubgroupError, '%s ! <= %s' % (
                        this.__class__.__name__, sg.__class__.__name__)
            else: # Dn
                try:
                    n = int(sgName[1:])
                    order = sg.order
                    if 2 * order == this.order:
                        return [
                            sg(setup = {
                                'axis_n': this.rotAxes['n'],
                                'axis_2': this.rotAxes[2][0]
                            })
                            # choosing other 2-fold axes leads essentially to
                            # the same.
                        ]
                    elif 2 * order > this.order:
                        return []
                    else:
                        assert False, 'TODO: %s (order %d)' % (sgName, order)
                        return [E()]
                except ValueError: # caused by int() function
                    assert False, 'TODO'
                    pass #TODO
                    # try C2nxCn
        elif sgName[0] == 'C':
            if sgName[-2:] == 'xI': # CnxI
                try:
                    n = int(sgName[1:-2])
                    if n == 2: # sg = C2xI
                        isoms = [
                            C2xI(setup = {'axis':this.rotAxes[2][i]})
                            for i in range(len(this.rotAxes[2]))
                        ]
                        if this.order % 8 == 0: # if D2xI, D4xI, etc
                            isoms.append(
                                CnxI(
                                    setup = {'n': n, 'axis': this.rotAxes['n']}
                                )
                            )
                        return isoms
                    order = sg.order
                    if 2 * order == this.order:
                        return [
                            CnxI(setup = {'n': n, 'axis': this.rotAxes['n']})
                        ]
                    elif 2 * order > this.order:
                        return []
                    else:
                        assert False, 'TODO: %s (order %d)' % (sgName, order)
                        return [E()]
                except ValueError: # caused by int() function
                    assert False, 'TODO'
                    pass #TODO
            else: # Cn
                try:
                    n = int(sgName[1:])
                    if n == 2: # sg = C2
                        isoms = [
                            C2(setup = {'axis':this.rotAxes[2][i]})
                            for i in range(len(this.rotAxes[2]))
                        ]
                        if this.order % 8 == 0: # if D2xI, D4xI, etc
                            isoms.append(
                                Cn(setup = {'n': n, 'axis': this.rotAxes['n']})
                            )
                        return isoms
                    order = sg.order
                    if 4 * order == this.order:
                        return [
                            Cn(setup = {'n': n, 'axis': this.rotAxes['n']})
                        ]
                    elif 4 * order > this.order:
                        return []
                    else:
                        assert False, 'TODO: %s (order %d)' % (sgName, order)
                        return [E()]
                except ValueError: # caused by int() function
                    raise ImproperSubgroupError, '%s ! <= %s' % (
                        this.__class__.__name__, sg.__class__.__name__)
                # try C2nxCn
        elif sg == ExI:
            return [ExI()]
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s(%s)' % (
                this.__class__.__name__, sg.__name__, sg.__class__.__name__)

# dynamically create DnxI classes:
class MetaDnxI(type):
    def __init__(this, classname, bases, classdict):
        type.__init__(this, classname, bases, classdict)
def DxI(n):
    if n == 1: return C2xI
    D_nxI = MetaDnxI('D%dxI' % n, (DnxI,),
            {
                'n'    : n,
                'order': 4 * n,
                'initPars': [
                        {
                            'type': 'vec3',
                            'par': 'axis',
                            'lab': "%d-fold axis" % n
                        }, {
                            'type': 'vec3',
                            'par': 'axis_2',
                            'lab': "axis of halfturn"
                        }
                    ]
            }
        )
    # TODO: fix subgroups depending on n:
    D_nxI.subgroups = [D_nxI, D(n), CxI(n), C2, ExI, E]
    if n != 2:
        D_nxI.subgroups.insert(-3, C(n))
    return D_nxI

D2xI = DxI(2)
D3xI = DxI(3)
D4xI = DxI(4)

class A4(Set):
    initPars = [
        {'type': 'vec3', 'par': 'o2axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o2axis1', 'lab': "half turn of orthogonal axis"}
    ]
    order = 12
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group A4, consisting of 12 rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - the identity E, and 3 orthogonal halfturns
        - 8 order 3 isometries.
        The group can be generated by the axes of 2 half turns, but this will
        not generate the group uniquely: There are 2 possibilities: the two
        tetrahedra in a Stella Octagula. The order of the 2 axes of the 2 half
        turns decides which position is obtained.
        """
        # A4 consists of:
        # 1. A subgroup D2: E, and half turns H0, H1, H2
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            assert len(isometries) == this.order, "%d != %d" % (
                                                this.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(this, isometries)
        else:
            axes = setup.keys()
            if 'o2axis0' in axes: o2axis0 = setup['o2axis0']
            else:                 o2axis0 = X[:]
            if 'o2axis1' in axes: o2axis1 = setup['o2axis1']
            else:                 o2axis1 = Y[:]
            d2 = generateD2(o2axis0, o2axis1)
            H0, H1, H2 = d2
            R1_1, R1_2, R2_1, R2_2, R3_1, R3_2, R4_1, R4_2 = generateA4O3(d2)

            Set.__init__(this, [
                    GeomTypes.E,
                    H0, H1, H2,
                    R1_1, R1_2, R2_1, R2_2, R3_1, R3_2, R4_1, R4_2
                ])

            this.rotAxes = {
                    2: [H0.axis(), H1.axis(), H2.axis()],
                    3: [R1_1.axis(), R2_1.axis(), R3_1.axis(), R4_1.axis()],
                }

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == C2:
            o2a = this.rotAxes[2]
            return [C2(setup = {'axis': a}) for a in o2a]
        elif sg == C3:
            o3a = this.rotAxes[3]
            return [C3(setup = {'axis': a}) for a in o3a]
        elif sg == A4:
            return [this]
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

class S4A4(A4):
    initPars = [
        {'type': 'vec3', 'par': 'o2axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o2axis1', 'lab': "half turn of orthogonal axis"}
    ]
    order = 24

    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group A4, consisting of 24 isometries, 12 direct, 12
        opposite.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - the identity E, and 3 orthogonal halfturns
        - 8 order 3 isometries.
        - 6 reflections
        - 6 rotary inversions
        The group can be generated by the axes of 2 half turns, but this will
        not generate the group uniquely: There are 2 possibilities: the two
        tetrahedra in a Stella Octagula. The order of the 2 axes of the 2 half
        turns decides which position is obtained.
        """
        # A4 consists of:
        # 1. A subgroup D2: E, and half turns H0, H1, H2
        #print 'isometries', isometries, 'setup', setup
        if isometries != None:
            assert len(isometries) == this.order, "%d != %d" % (
                                                this.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(this, isometries)
        else:
            axes = setup.keys()
            if 'o2axis0' in axes: o2axis0 = setup['o2axis0']
            else:                 o2axis0 = X[:]
            if 'o2axis1' in axes: o2axis1 = setup['o2axis1']
            else:                 o2axis1 = Y[:]
            d2 = generateD2(o2axis0, o2axis1)
            h0, h1, h2 = d2
            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = generateA4O3(d2)

            ax0 = h0.axis()
            ax1 = h1.axis()
            ax2 = h2.axis()
            ri0_1 = GeomTypes.RotInv3(axis = ax0, angle = qTurn)
            ri0_3 = GeomTypes.RotInv3(axis = ax0, angle = 3*qTurn)
            ri1_1 = GeomTypes.RotInv3(axis = ax1, angle = qTurn)
            ri1_3 = GeomTypes.RotInv3(axis = ax1, angle = 3*qTurn)
            ri2_1 = GeomTypes.RotInv3(axis = ax2, angle = qTurn)
            ri2_3 = GeomTypes.RotInv3(axis = ax2, angle = 3*qTurn)
            pn0 = GeomTypes.Rot3(axis = ax0, angle = eTurn) * ax1
            pn1 = GeomTypes.Rot3(axis = ax0, angle = 3*eTurn) * ax1
            pn2 = GeomTypes.Rot3(axis = ax1, angle = eTurn) * ax0
            pn3 = GeomTypes.Rot3(axis = ax1, angle = 3*eTurn) * ax0
            pn4 = GeomTypes.Rot3(axis = ax2, angle = eTurn) * ax0
            pn5 = GeomTypes.Rot3(axis = ax2, angle = 3*eTurn) * ax0
            s0 = GeomTypes.Refl3(planeN = pn0)
            s1 = GeomTypes.Refl3(planeN = pn1)
            s2 = GeomTypes.Refl3(planeN = pn2)
            s3 = GeomTypes.Refl3(planeN = pn3)
            s4 = GeomTypes.Refl3(planeN = pn4)
            s5 = GeomTypes.Refl3(planeN = pn5)
            Set.__init__(this, [
                    GeomTypes.E,
                    h0, h1, h2,
                    r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2,
                    s0, s1, s2, s3, s4, s5,
                    ri0_1, ri0_3, ri1_1, ri1_3, ri2_1, ri2_3,
                ])

            this.reflNormals = [pn0, pn1, pn2, pn3, pn4, pn5]
            this.rotAxes = {
                    2: [h0.axis(), h1.axis(), h2.axis()],
                    3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()],
                }

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        sgName = sg.__name__
        #S4A4, A4, D2nDn, DnCn, C2nCn, Dn, Cn
        #C3, C2, E
        if sg == C2:
            return [C2(setup = {'axis': a}) for a in this.rotAxes[2]]
        elif sg == C3:
            return [C3(setup = {'axis': a}) for a in this.rotAxes[3]]
        elif sg == A4:
            o2a = this.rotAxes[2]
            return [
                A4(setup = {'o2axis0': o2a[0], 'o2axis1': o2a[1]}),
            ]
        elif sg == S4A4:
            return [this]
        elif sg == C4C2:
            return [C4C2(setup = {'axis': a}) for a in this.rotAxes[2]]
        elif sg == C2C1:
            return [
                C2C1(setup = {'axis': normal}) for normal in this.reflNormals
            ]
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

# Dn = D2, (D1~C2)
# Cn = C3, C2
# D2nDn = D4D2
# DnCn  = D3C3, D2C2
# C2nCn = C4C2, C2C1
S4A4.subgroups = [S4A4, A4,
        #D2nDn, DnCn, C2nCn,
        #Dn, Cn
        C4C2,
        C3,
        C2C1, C2,
        E
    ]

class A4xI(A4):
    initPars = [
        {'type': 'vec3', 'par': 'o2axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o2axis1', 'lab': "half turn of orthogonal axis"}
    ]
    order = 24
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group A4xI, consisting of 12 rotations and 12 rotary
        inversions.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - the identity E, and 3 orthogonal halfturns
        - 8 order 3 rotations.
        - the central inversion I, 3 reflections
        - 8 order rotary inversions
        The group can be generated by the axes of 2 half turns
        """
        if isometries != None:
            assert len(isometries) == this.order, "%d != %d" % (
                                                this.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(this, isometries)
        else:
            a4 = A4(setup = setup)
            Set.__init__(this, a4 * ExI())
            this.rotAxes = a4.rotAxes

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == C2:
            o2a = this.rotAxes[2]
            return [C2(setup = {'axis': a}) for a in o2a]
        elif sg == C3:
            o3a = this.rotAxes[3]
            return [C3(setup = {'axis': a}) for a in o3a]
        if sg == C2xI:
            o2a = this.rotAxes[2]
            return [C2xI(setup = {'axis': a}) for a in o2a]
        elif sg == C3xI:
            o3a = this.rotAxes[3]
            return [C3xI(setup = {'axis': a}) for a in o3a]
        elif sg == A4:
            # the other ways of orienting A4 into A4xI doesn't give anything new
            return [
                A4(
                    setup = {
                        'o2axis0': this.rotAxes[2][0],
                        'o2axis1': this.rotAxes[2][1]
                    }
                )
            ]
        elif sg == A4xI:
            return [this]
        elif sg == ExI:
            return [ExI()]
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

class S4(Set):
    initPars = [
        {'type': 'vec3', 'par': 'o4axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o4axis1', 'lab': "half turn of orthogonal axis"}
    ]
    order = 24
    def __init__(this, isometries = None, setup = {}):
        """
        The algebraic group S4, consisting of 24 rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class initPars argument.
        Contains:
        - the identity E,
        - and 9 orthogonal turns based on quarter turns (1/4, 1/2, 3/4)
        - 8 turns based on third turns (1/3, 2/3).
        - 6 halfturns
        The group can be generated by the axes of 2 quarter turns,
        """
        if isometries != None:
            assert len(isometries) == this.order, "%d != %d" % (
                                                this.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(this, isometries)
        else:
            axes = setup.keys()
            if 'o4axis0' in axes: o4axis0 = setup['o4axis0']
            else:                 o4axis0 = X[:]
            if 'o4axis1' in axes: o4axis1 = setup['o4axis1']
            else:                 o4axis1 = Y[:]
            d2 = generateD2(o4axis0, o4axis1)
            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = generateA4O3(d2)
            q0_2, q1_2, q2_2 = d2
            ax0 = q0_2.axis()
            ax1 = q1_2.axis()
            ax2 = q2_2.axis()
            q0_1 = GeomTypes.Rot3(axis = ax0, angle = qTurn)
            q0_3 = GeomTypes.Rot3(axis = ax0, angle = 3*qTurn)
            q1_1 = GeomTypes.Rot3(axis = ax1, angle = qTurn)
            q1_3 = GeomTypes.Rot3(axis = ax1, angle = 3*qTurn)
            q2_1 = GeomTypes.Rot3(axis = ax2, angle = qTurn)
            q2_3 = GeomTypes.Rot3(axis = ax2, angle = 3*qTurn)
            h0 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax0, angle = eTurn) * ax1,
                    angle = hTurn
                )
            h1 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax0, angle = 3*eTurn) * ax1,
                    angle = hTurn
                )
            h2 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax1, angle = eTurn) * ax0,
                    angle = hTurn
                )
            h3 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax1, angle = 3*eTurn) * ax0,
                    angle = hTurn
                )
            h4 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax2, angle = eTurn) * ax0,
                    angle = hTurn
                )
            h5 = GeomTypes.Rot3(
                    axis = GeomTypes.Rot3(axis = ax2, angle = 3*eTurn) * ax0,
                    angle = hTurn
                )
            Set.__init__(this, [
                    GeomTypes.E,
                    q0_1, q0_2, q0_3, q1_1, q1_2, q1_3, q2_1, q2_2, q2_3,
                    r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2,
                    h0, h1, h2, h3, h4, h5
                ])
            this.rotAxes = {
                    2: [h0.axis(), h1.axis(), h2.axis(),
                            h3.axis(), h4.axis(), h5.axis()
                        ],
                    3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()],
                    4: [ax0, ax1, ax2]
                }

    def realiseSubgroups(this, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == C2:
            o2a = this.rotAxes[2]
            o4a = this.rotAxes[4]
            return [C2(setup = {'axis': a}) for a in o2a].extend(
                    [C2(setup = {'axis': a}) for a in o4a]
                )
        elif sg == C3:
            o3a = this.rotAxes[3]
            return [C3(setup = {'axis': a}) for a in o3a]
        elif sg == C4:
            o4a = this.rotAxes[4]
            return [C4(setup = {'axis': a}) for a in o4a]
        elif sg == A4:
            # the other ways of orienting A4 into A4xI doesn't give anything new
            return [
                A4(
                    setup = {
                        'o2axis0': this.rotAxes[4][0],
                        'o2axis1': this.rotAxes[4][1]
                    }
                )
            ]
        elif sg == S4:
            return [this]
        elif sg == E:
            return [E()]
        else: raise ImproperSubgroupError, '%s ! <= %s' % (
                this.__class__.__name__, sg.__class__.__name__)

def generateD2(o2axis0, o2axis1):
    """
    Returns 3 orthogonal halfturns for D2
    """
    # if axes is specified as a transform:
    if isinstance(o2axis0, GeomTypes.Transform3):
        o2axis0 = o2axis0.axis()
    if isinstance(o2axis1, GeomTypes.Transform3):
        o2axis1 = o2axis1.axis()
    assert GeomTypes.eq(GeomTypes.Vec3(o2axis0) * GeomTypes.Vec3(o2axis1), 0), (
            "Error: axes not orthogonal")
    H0 = GeomTypes.HalfTurn3(o2axis0)
    H1 = GeomTypes.Rot3(axis = o2axis1, angle = hTurn)
    return (H0, H1, H1 * H0)

def generateA4O3(D2HalfTurns):
    """
    Returns a tuple (R1_1_3, R1_2_3, R2_1_3, R2_2_3, R3_1_3, R3_2_3, R4_1_3,
    R4_2_3)

    D2HalfTurns: tuple containing H0, H1, H2
    """
    H0, H1, H2 = D2HalfTurns

    # the one order 3 rotation axis, is obtained as follows:
    # imagine A4 is part of S4 positioned in a cube
    # H0, H1, H2 go through the cube face centres
    # define a quarter turn around H2
    Q = GeomTypes.Rot3(axis = H2.axis(), angle = qTurn)
    # h0 and h1 go through cube edge centres
    h0 = Q * H0
    h1 = Q * H1
    # o3axis goes through 1 of the 2 cube vertices that form the edge
    # between the faces which centres are on H0 and H1
    o3axis = GeomTypes.Rot3(
            axis = h0.axis(), angle = asin_1_V3
        ) * h1.axis()
    # R1_1_3: 1/3 rotation around the first order 3 axis
    # R1_2_3: 2/3 rotation around the first order 3 axis
    R1_1_3 = GeomTypes.Rot3(axis = o3axis, angle = tTurn)
    R1_2_3 = GeomTypes.Rot3(axis = o3axis, angle = 2*tTurn)
    R4_1_3 = R1_1_3 * H0
    R3_1_3 = R1_1_3 * H1
    R2_1_3 = R1_1_3 * H2
    R2_2_3 = R1_2_3 * H0
    R4_2_3 = R1_2_3 * H1
    R3_2_3 = R1_2_3 * H2
    # print 'R1_1_3', R1_1_3
    # print 'R1_2_3', R1_2_3
    # print 'R2_1_3', R2_1_3
    # print 'R2_2_3', R2_2_3
    # print 'R3_1_3', R3_1_3
    # print 'R3_2_3', R3_2_3
    # print 'R4_1_3', R4_1_3
    # print 'R5_2_3', R4_2_3
    return (R1_1_3, R1_2_3, R2_1_3, R2_2_3, R3_1_3, R3_2_3, R4_1_3, R4_2_3)

__order = {
    E:      1,
    ExI:    2,
    A4:    12,
    A4xI:  24,
    S4A4:  24,
    S4:    24,
}
def order(isometry):
    try:
        return __order[isometry]
    except KeyError:
        return isometry.order

E.subgroups = [E]
ExI.subgroups = [ExI, E]
#TODO:
Cn.subgroups = [Cn, E]
CnxI.subgroups = [CnxI, Cn, ExI, E]
C2nCn.subgroups = [C2nCn, Cn, E]
Dn.subgroups = [Dn, Cn, C2, E]
DnxI.subgroups = [DnxI, Dn, CnxI, Cn, C2xI, C2, ExI, E]

# Dn = D2, (D1~C2)
# Cn = C3, C2
A4.subgroups = [A4,
        #Dn,
        C3, C2, E
    ]

# DnxI = D2xI, D1xI
# CnxI = C3xI, C2xI
# Dn = D2, (D1~C2)
# Cn = C3
A4xI.subgroups = [A4xI, A4,
        #TODO: DnxI, Dn,
        C3xI, C2xI,
        C3, C2, ExI, E
    ]

# Dn = D4, D3, D2 (2x), D1 (@ order 4)
# Cn = C4, C3, C2 (@ order 2)
S4.subgroups = [S4, A4,
        #Dn,
        C4, C3, C2, E
    ]

if __name__ == '__main__':

    print 'testing creation of set',
    g = Set([Hx, Hy])
    print '....ok'
    #print 'Initialised set g:', g
    print "testing 'in' relation",
    assert GeomTypes.Rot3(axis = [1, 0, 0], angle = hTurn) in g
    assert GeomTypes.Rot3(axis = [-1, 0, 0], angle = -hTurn) in g
    print '......ok'
    print "testing 'close' function",
    cg = g.close()
    #print 'Set g after closing:'
    #print cg
    assert len(cg) == 4
    assert Hx in cg
    assert Hy in cg
    assert Hz in cg
    assert GeomTypes.E in cg
    print '...ok'

    print 'testing creation of set',
    g = Set([GeomTypes.Rot3(axis = X, angle = qTurn)])
    print '....ok'
    print "testing 'in' relation",
    GeomTypes.Rot3(axis =  X, angle = qTurn)  in g
    GeomTypes.Rot3(axis = -X, angle = -qTurn) in g
    print '......ok'
    print "testing 'close' function",
    cg = g.close()
    #print 'Set g after closing:'
    #print cg
    assert len(cg) == 4
    GeomTypes.Rot3(axis =  GeomTypes.Vec3([1, 0, 0]), angle = qTurn)  in cg
    GeomTypes.Rot3(axis = -GeomTypes.Vec3([1, 0, 0]), angle = -qTurn) in cg
    assert Hx in cg
    assert GeomTypes.E in cg
    print '...ok'

    print 'testing creation of A4',
    a4 = A4(setup = setup(o2axis0 = X, o2axis1= Y))
    print '.....ok'
    print 'checking result',
    assert len(a4) == 12
    assert GeomTypes.E in a4
    assert Hx in a4
    assert Hy in a4
    assert Hz in a4
    t0 = GeomTypes.Rot3(axis = [1,  1,  1], angle =   tTurn)
    assert t0 in a4
    t1 = GeomTypes.Rot3(axis = [1,  1,  1], angle = 2*tTurn)
    assert t1 in a4
    t2 = GeomTypes.Rot3(axis = [1, -1,  1], angle =   tTurn)
    assert t2 in a4
    t3 = GeomTypes.Rot3(axis = [1, -1,  1], angle = 2*tTurn)
    assert t3 in a4
    t4 = GeomTypes.Rot3(axis = [1, -1, -1], angle =   tTurn)
    assert t4 in a4
    t5 = GeomTypes.Rot3(axis = [1, -1, -1], angle = 2*tTurn)
    assert t5 in a4
    t6 = GeomTypes.Rot3(axis = [1,  1, -1], angle =   tTurn)
    assert t6 in a4
    t7 = GeomTypes.Rot3(axis = [1,  1, -1], angle = 2*tTurn)
    assert t7 in a4
    print '............ok'

    print 'testing creation of A4',
    a4 = A4(
            setup = setup(
                # try list argument
                o2axis0 = [1, 1, 1],
                # try Rot3 argument
                o2axis1 = GeomTypes.HalfTurn3([1, -1, 0])
            )
        )
    #print 'A4(o2axis0 = [1, 1, 1], o2axis1 = [1, -1, 0])'
    print '.....ok'
    # this a4 is the above a4 repositioned as follows:
    r0 = GeomTypes.Rot3(axis = Z, angle = eTurn)
    r1 = GeomTypes.Rot3(axis = [1, -1, 0], angle = math.atan(1/math.sqrt(2)))
    r = r1 * r0
    print 'checking result',
    assert len(a4) == 12
    assert GeomTypes.E in a4
    assert GeomTypes.HalfTurn3(r*X) in a4
    assert GeomTypes.HalfTurn3(r*Y) in a4
    assert GeomTypes.HalfTurn3(r*Z) in a4
    assert GeomTypes.Rot3(axis = r * t0.axis(), angle =   tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t1.axis(), angle = 2*tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t2.axis(), angle =   tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t3.axis(), angle = 2*tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t4.axis(), angle =   tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t5.axis(), angle = 2*tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t6.axis(), angle =   tTurn) in a4
    assert GeomTypes.Rot3(axis = r * t7.axis(), angle = 2*tTurn) in a4
    print '............ok'
    #print a4
    print 'test grouping this',
    ca4 = copy(a4)
    a4.group(2)
    assert a4 == ca4
    print '.........ok'

    ########################################################################
    # Quotient Set:
    a4 = A4(setup = setup(o2axis0 = X, o2axis1= Y))
    assert len(a4) == 12
    # print 'group a4:'
    # print a4
    d2 = Set([Hx, Hy])
    d2.group()
    assert len(d2) == 4
    # print 'has a subgroup D2:'
    # print d2
    print 'test quotient set: A4/D2',
    q = a4 / d2
    # print 'which defines a right quotient set s = ['
    for s in q:
    #     print '  set('
    #     for e in s:
    #         print '    ', e
    #     print '  )'
        assert len(s) == 4
    # print ']'
    assert len(q) == 3
    # check if A4 / D2 is a partition of A4:
    for i in range(len(q)-1):
        s = q[i]
        for transform in s:
            for j in range(i+1, len(q)):
                assert not transform in q[j]
    print '...ok'

    ########################################################################
    # Quotient Set:
    print 'test isSubgroup: A4, S4',
    s4 = S4()
    a4 = A4()
    assert a4.isSubgroup(s4)
    assert not s4.isSubgroup(a4)
    a4.add(GeomTypes.I)
    assert not a4.isSubgroup(s4)
    print '....ok'

    print 'success!'
