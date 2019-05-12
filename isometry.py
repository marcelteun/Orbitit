#! /usr/bin/python
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
#------------------------------------------------------------------
from __future__ import print_function

from copy import copy, deepcopy
import math

import geomtypes

X = geomtypes.UX
Y = geomtypes.UY
Z = geomtypes.UZ

INIT_PARS = {
    'Cn': [
        {'type': 'int', 'par': 'n', 'lab': "order"},
        {'type': 'vec3', 'par': 'axis', 'lab': "{}-fold axis"}
    ],
    'DnCn': [
        {'type': 'int', 'par': 'n', 'lab': "order"},
        {'type': 'vec3', 'par': 'axis_n', 'lab': "{}-fold axis"},
        {'type': 'vec3', 'par': 'normal_r', 'lab': "normal of reflection"}
    ],
    'Dn': [
        {'type': 'int', 'par': 'n', 'lab': "order"},
        {'type': 'vec3', 'par': 'axis_n', 'lab': "{}-fold axis"},
        {'type': 'vec3', 'par': 'axis_2', 'lab': "axis of halfturn"}
    ],
    'A4': [
        {'type': 'vec3', 'par': 'o2axis0', 'lab': "half turn axis"},
        {'type': 'vec3', 'par': 'o2axis1', 'lab': "half turn of orthogonal axis"}
    ],
    'A5': [
        {'type': 'vec3', 'par': 'o3axis', 'lab': "3-fold axis"},
        {'type': 'vec3', 'par': 'o5axis', 'lab': "5-fold axis (nearest)"}
    ],
    'S4': [
        {'type': 'vec3', 'par': 'o4axis0', 'lab': "4-fold axis"},
        {'type': 'vec3', 'par': 'o4axis1', 'lab': "orthogonal 4-fold axis"}
    ]
}

STD_SETUP = {
    'Cn': {'n': None, 'axis': Z[:]},
    'DnCn': {'n': None, 'axis_n': Z[:], 'normal_r': X[:]},
    'Dn': {'n': None, 'axis_n': Z[:], 'axis_2': X[:]},
    'A4': {'o2axis0': X[:], 'o2axis1': Y[:]},
    'A5': {'o3axis': geomtypes.Vec3([1, 1, 1]),
           'o5axis': geomtypes.Vec3([0, (1.0 + math.sqrt(5))/2, 1])},
    'S4': {'o4axis0': X[:], 'o4axis1': Y[:]}
}

def _init_pars(sym, order=None):
    pars = deepcopy(INIT_PARS[sym])
    if order:
        pars[1]['lab'] = pars[1]['lab'].format(order)
    return pars

def _std_setup(sym, order=None):
    setup = deepcopy(STD_SETUP[sym])
    if order:
        setup['n'] = order
    return setup

HALFTURN = geomtypes.HALF_TURN
QUARTER_TURN = geomtypes.QUARTER_TURN
EIGHTH_TURN = QUARTER_TURN / 2
THIRD_TURN = geomtypes.THIRD_TURN

acos_1_V3 = math.acos(1.0 / math.sqrt(3))
asin_1_V3 = math.asin(1.0 / math.sqrt(3))
asin_V2_V3 = acos_1_V3
acos_V2_V3 = asin_1_V3

I = geomtypes.I  # central inversion

__Cn_metas = {}
__C2nCn_metas = {}
__CnxI_metas = {}
__DnCn_metas = {}
__Dn_metas = {}
__DnxI_metas = {}
__D2nDn_metas = {}


def _sort_and_del_dups(g):
    """Sort list of isometry classes and remove duplicates"""
    # remove duplicates first (unsorts the list):
    g = list(dict.fromkeys(g))
    g.sort(key=lambda x: x.order, reverse=True)
    return g

class ImproperSubgroupError(ValueError):
    "Raised when subgroup is not really a subgroup"

class Set(set):

    debug = False
    mixed = False # if True the isometry set consists of direct and indirect
                  # isometries else it consists of direct isometries only if it
                  # is a group.
    std_setup = None

    def __init__(self, *args):
        try:
            self.generator
        except AttributeError:
            self.generator = {}
        set.__init__(self, *args)
        self.short_string = True

    def __repr__(self):
        s = '%s([\n' % (self.__class__.__name__)
        for e in self:
            s = '%s  %s,\n' % (s, repr(e))
        s = '%s])' % s
        if __name__ != '__main__':
            s = '%s.%s' % (__name__, s)
        return s

    def __str__(self):
        def to_s():
            s = '%s([\n' % (self.__class__.__name__)
            for e in self:
                s = '%s  %s,\n' % (s, str(e))
            s = '%s])' % s
            if __name__ != '__main__':
                s = '%s.%s' % (__name__, s)
            return s
        if self.generator != {}:
            if self.short_string:
                s = '%s(setup=%s)' % (self.__class__.__name__,self.generator)
            else:
                s = to_s()
        else:
            s = to_s()
        return s

    def __eq__(self, o):
        eq = (len(self) == len(o))
        if eq:
            for e in self:
                eq = e in o
                if not eq: break
        return eq

    def __sub__(self, o):
        new = Set([])
        for e in self:
            if e not in o:
                set.add(new, e)
        return new

    def __or__(self, o):
        new = Set(self)
        for e in o:
            new.add(e)
        return new

    def __mul__(self, o):
        if isinstance(o, Set):
            # Set(self) * Set(o)
            new = Set([])
            for d in o:
                new.update(self * d)
            return new
        else:
            # Set * geomtypes.Transform3
            return Set([e * o for e in self])

    def __rmul__(self, o):
        # Note rotation Set * Set is caught by __mul__
        # rotation Rot * Set
        return Set([o * e for e in self])

    def is_group(self):
        if len(self) == 0: return False
        this_is_group = True
        for e in self:
            # optimised away, done as part of next loop:
            # if not (e.inverse() in self):
            this_has_inverse = False
            for o in self:
                this_has_inverse  = this_has_inverse | (e.inverse() == o)
                is_closed_for_this = e*o in self and o*e in self
                if not is_closed_for_this:
                    break;
            if not this_has_inverse or not is_closed_for_this:
                this_is_group = False
                break;

        return this_is_group
        # the following is not needed to check, is done implicitly:
        # and (geomtypes.E in self)

    def is_subgroup(self, o, checkGroup = True):
        """returns whether this is a subgroup of o)"""
        if len(self) > len(o): return False # optimisation
        return (
                (not checkGroup) or self.is_group()
            ) and self.issubset(o)

    def subgroup(self, o):
        try:
            if isinstance(o, geomtypes.Transform3):
                # generate the quotient set THIS / o
                assert o in self
                subgroup = Set([o])
                subgroup.group()
                return subgroup
            else:
                # o is already a set
                for e in o:
                    assert e in self, '%s not in %s' % (e,
                        self.__class__.__name__)
                subgroup = copy(o)
                # for optimisation: don't call group (slow) for self == o:
                if len(subgroup) < len(self):
                    subgroup.group()
                elif len(subgroup) > len(self):
                    raise ImproperSubgroupError, \
                        '{} not subgroup of {} (with this orientation)'.format(
                            o.__class__.__name__, self.__class__.__name__)
                return subgroup
        #except ImproperSubgroupError:
        except AssertionError:
            raise ImproperSubgroupError, \
                '{} not subgroup of {} (with this orientation)'.format(
                    o.__class__.__name__, self.__class__.__name__)

    def __div__(self, o):
        # this * subgroup: right quotient set
        # make sure o is a subgroup:
        if (len(o) > len(self)): return o.__div__(self)
        o = self.subgroup(o)
        assert len(o) <= len(self)
        # use a list of sets, since sets are unhashable
        quotientSet = []
        # use a big set for all elems found so for
        foundSoFar = Set([])
        for te in self:
            q = te * o
            if q.get_one() not in foundSoFar:
                quotientSet.append(q)
                foundSoFar = foundSoFar.union(q)
        return quotientSet

    quotientSet = __div__

    def __rdiv__(self, o):
        #  subgroup * self: left quotient set
        pass # TODO

    def __contains__(self, o):
        # Needed for 'in' relationship: default doesn't work, it seems to
        # compare the elements id.
        for e in self:
            if e == o:
                return True
        return False

    def add(self, e):
        l = len(self)
        if e not in self:
            set.add(self, e)

    def update(self, o):
        for e in o:
            self.add(e)

    def get_one(self):
        for e in self: return e

    def group(self, maxIter = 50):
        """
        Tries to make a group out of the set of isometries

        If it succeeds within maxiter step this set is closed, contains the unit
        element and the set contains for every elements its inverse
        """
        result = copy(self)
        for e in self:
            result.add(e.inverse())
        result.add(geomtypes.E)
        self.clear()
        self.update(result.close(maxIter))

    def close(self, maxIter = 5):
        """
        Return a set that is closed, if it can be generated within maxIter steps.
        """
        result = copy(self)
        for i in range(maxIter):
            lPrev = len(result)
            result.update(result * result)
            l = len(result)
            if l == lPrev:
                break
        assert (l == lPrev), "couldn't close group after %d iterations"% maxIter
        return result

    def checkSetup(self, setup):
        if setup != {} and self.init_pars == []:
            print("Warning: class {} doesn't handle any setup pars {}".format(
                    self.__class__.__name__, setup.keys()))
        for k in setup.keys():
            found = False
            for p in self.init_pars:
                found |= p['par'] == k
                if found: break
            if not found:
                print("Warning: unknown setup parameter {} "
                    "for class {}".format(k, self.__class__.__name__))
                assert False, 'Got setup = %s' % str(setup)
        self.generator = setup

    @property
    def setup(self):
        return self.generator

def init_dict(**kwargs): return kwargs

class E(Set):
    init_pars = []
    order = 1
    mixed = False
    def __init__(self, isometries=None, setup=None):
        if setup is None:
            setup = {}
        self.checkSetup(setup)
        Set.__init__(self, [geomtypes.E])

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        return [E()]

E.subgroups = [E]

class ExI(Set):
    init_pars = []
    order = 2
    mixed = True
    directParent = E
    direct_parent_setup = {}
    def __init__(self, isometries=None, setup=None):
        if setup is None:
            setup = {}
        self.checkSetup(setup)
        Set.__init__(self, [geomtypes.E, geomtypes.I])

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == ExI:
            return [self]
        elif sg == E:
            return [E()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)

ExI.subgroups = [ExI, E]

def _Cn_get_subgroups(n):
    """Add subgroup classes of Cn (with specific n, except own class)

    The own class (by calling C(n) cannot be added, since it leads to
    recursion.
    """
    G = [C(i) for i in range(n/2, 0, -1) if n % i == 0]
    return G

class MetaCn(type):
    """Meta class for the algebraic group of class Cn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)

class Cn(Set):
    """Class for the C2 symmetry group"""
    __metaclass__ = MetaCn
    init_pars = _init_pars('Cn', 'n')
    std_setup = _std_setup('Cn', 2)
    order = 0
    n = 0
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group Cn, consisting of n rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        """
        if setup is None:
            setup = {}
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            keys = setup.keys()
            if 'axis' in keys: axis = setup['axis']
            else:              axis = copy(self.std_setup['axis'])
            if self.n != 0   : n = self.n
            else:
                if 'n' in keys: n = setup['n']
                else:           n = copy(self.std_setup['n'])
                if n == 0: n = 1
                # If self.n is hard-code (e.g. for C3)
                # then if you specify n it should be the correct value
                assert self.n == 0 or n == self.n
                self.n = n

            angle = 2 * math.pi / n
            try:
                r = geomtypes.Rot3(axis=axis, angle=angle)
            except TypeError:
                # assume axis has Rot3 type
                r = geomtypes.Rot3(axis=axis.axis(), angle=angle)

            isometries = [r]
            for i in range(n-1):
                isometries.append(r * isometries[-1])
            Set.__init__(self, isometries)
            self.order = n
            self.rot_axes = {'n': axis}
            self.subgroups = _Cn_get_subgroups(n)
            self.subgroups.insert(0, C(n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == E:
            return [E()]
        if sg.n > self.n:
            return []
        if isinstance(sg, MetaCn):
            if sg.n == self.n: # Cn
                return [self]
            else:
                return[sg(setup={'axis': self.rot_axes['n']})]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)


# dynamically create Cn classes:
def C(n):
    """Create class for Cn with specific n"""
    try:
        return __Cn_metas[n]
    except KeyError:
        if n == 1:
            __Cn_metas[n] = E
        else:
            c_n = MetaCn('C%d' % n, (Cn,),
                    {
                        'n'    : n,
                        'order': n,
                        'mixed': False,
                        'init_pars': _init_pars('Cn', n),
                        'std_setup': _std_setup('Cn', n)
                    }
                )
            c_n.subgroups = _Cn_get_subgroups(n)
            c_n.subgroups.insert(0, c_n)
            __Cn_metas[n] = c_n
        return __Cn_metas[n]

def _C2nCn_get_subgroups(n):
    """Add subgroup classes of C2nCn (with specific n, except own class)

    The own class (by calling C(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n/2, 0, -1) if n % i == 0]
    m = n / 2
    if n % 2 != 0:
        # n odd: group has a reflection
        # CnxI: all divisors are also odd, i.e. they miss reflection
        # C2nCn: none, there are no even divisors
        g_c2ici = [C2nC(i) for i in divs if i % 2 != 0]
        g = (g_c2ici)
    else:
        # n even: group has no reflection
        # CnxI: only add divisors that are odd if n/i is odd too
        #       but since n even, n/i even too. No such subgroup.
        # C2nCn: only add divisors that are even if n/i is odd.
        g_c2ici = [C2nC(i) for i in divs
                   if i % 2 == 0 and (n / i) % 2 != 0]
        g = (g_c2ici)
    divs.insert(0, n)
    g.extend([C(i) for i in divs])
    return _sort_and_del_dups(g)

class MetaC2nCn(type):
    """Meta class for the algebraic group of class C2nCn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)

class C2nCn(Set):
    """Class for the C2nCn symmetry group"""
    __metaclass__ = MetaC2nCn
    init_pars = _init_pars('Cn', 'n')
    std_setup = _std_setup('Cn', 2)
    order = 0
    n = 0
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group C2nCn, consisting of n rotations and of n rotary
        inversions (reflections)

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n rotary inversions around one n-fold axis (angle: pi(1 + 2i)/n, with
          0 <= i < n)
        """
        if setup is None:
            setup = {}
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            s = copy(setup)
            # TODO remove dependency on n, make this class C2nCn internal, use
            # only C2nC(n) and rename this to an __
            if 'n' not in s and self.n != 0:
                s['n'] = self.n
            # If self.n is hard-code (e.g. for C6C3)
            # then if you specify n it should be the correct value
            assert self.n == 0 or s['n'] == self.n
            # TODO use direct parent here... (no dep on n)
            cn = Cn(setup=s)
            self.direct_parent_setup = copy(s)
            self.n = cn.n
            s['n'] = 2 * s['n']
            c2n = Cn(setup=s)
            Set.__init__(self, cn | ((c2n-cn) * geomtypes.I))
            self.rot_axes = {'n': cn.rot_axes['n']}
            self.order = c2n.order
            self.subgroups = _C2nCn_get_subgroups(self.n)
            self.subgroups.insert(0, C2nC(self.n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if isinstance(sg, MetaC2nCn):
            if sg.n == self.n: # C2cCn
                return [self]
            else:
                return [sg(setup={'axis': self.rot_axes['n']})]
        elif isinstance(sg, MetaCn):
            return [sg(setup={'axis': self.rot_axes['n']})]
        elif sg == E:
            return [E()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)


# dynamically create C2nCn classes:
def C2nC(n):
    """Create class for CnxI with specific n"""
    try:
        return __C2nCn_metas[n]
    except KeyError:
        c_2n_c_n = MetaC2nCn('C%dC%d' % (2*n, n), (C2nCn,),
                {
                    'n'    : n,
                    'order': 2 * n,
                    'mixed': True,
                    'directParent': C(n),
                    'init_pars': _init_pars('Cn', n),
                    'std_setup': _std_setup('Cn', n)
                }
            )
        c_2n_c_n.subgroups = _C2nCn_get_subgroups(n)
        c_2n_c_n.subgroups.insert(0, c_2n_c_n)
        __C2nCn_metas[n] = c_2n_c_n
        return __C2nCn_metas[n]

def _CnxI_get_subgroups(n):
    """Add subgroup classes of CnxI (with specific n, except own class)

    The own class (by calling C(n) cannot be added, since it leads to
    recursion.
    """
    # divisors of n
    divs = [i for i in range(n/2, 0, -1) if n % i == 0]
    # Note:
    # - OK if n odd (only odd divisors): always mapping on rotated version
    # - OK if n even:
    #     * odd divisor: since n even the rotated version of the divisor is
    #                    included.
    #     * even divisor: trivial, same as n
    g = [CxI(i) for i in divs]
    g_cn = [C(i) for i in divs]
    g_cn.insert(0, C(n))
    g.extend(g_cn)
    # C2nCn:
    if n % 2 == 0:
        # n even: group contains a reflection
        m = n / 2
        # - if odd divisor: trivial, also have reflection
        # - if even divisor i: can only be added if (n / i) % 2 == 0
        g_c2ici = [C2nC(i) for i in range(1, m + 1)
                   if n % i == 0 and (i % 2 != 0 or (n / i) % 2 == 0)]
        g.extend(g_c2ici)
    # else: n odd: all divisors are odd as well: all C2iCi for divisors i will
    # have a reflection, while CnxI doesn't
    return _sort_and_del_dups(g)

class MetaCnxI(type):
    """Meta class for the algebraic group of class CnxI"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)

class CnxI(Set):
    """Class for the CnxI symmetry group"""
    __metaclass__ = MetaCnxI
    init_pars = _init_pars('Cn', 'n')
    std_setup = _std_setup('Cn', 2)
    order = 0
    n = 0
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group CnxI, consisting of n rotations and of n rotary
        inversions (reflections)

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n rotary inversions around one n-fold axis (angle: i * 2pi/n, with
          0 <= i < n)
        """
        if setup is None:
            setup = {}
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            s = copy(setup)
            if 'n' not in s and self.n != 0:
                s['n'] = self.n
            # If self.n is hard-code (e.g. for C3xI)
            # then if you specify n it should be the correct value
            assert self.n == 0 or s['n'] == self.n
            cn = Cn(setup=s)
            self.direct_parent_setup = copy(s)
            self.n = cn.n
            Set.__init__(self, cn * ExI())
            self.rot_axes = {'n': cn.rot_axes['n']}
            self.order = 2 * cn.order
            self.subgroups = _CnxI_get_subgroups(self.n)
            self.subgroups.insert(0, CxI(self.n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if isinstance(sg, MetaCnxI):
            if sg.n == self.n: # CnxI
                return [self]
            return [sg(setup={'axis': self.rot_axes['n']})]
        elif isinstance(sg, (MetaC2nCn, MetaCn)):
            return [sg(setup={'axis': self.rot_axes['n']})]
        elif sg == ExI:
            return [ExI()]
        elif sg == E:
            return [E()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)


# dynamically create CnxI classes:
def CxI(n):
    """Create class for CnxI with specific n"""
    try:
        return __CnxI_metas[n]
    except KeyError:
        if n == 1:
            __CnxI_metas[n] = ExI
        else:
            c_nxi = MetaCnxI('C%dxI' % n, (CnxI,),
                    {
                        'n'    : n,
                        'order': 2 * n,
                        'mixed': True,
                        'directParent': C(n),
                        'init_pars': _init_pars('Cn', n),
                        'std_setup': _std_setup('Cn', n)
                    }
                )
            c_nxi.subgroups = _CnxI_get_subgroups(n)
            c_nxi.subgroups.insert(0, c_nxi)
            __CnxI_metas[n] = c_nxi
        return __CnxI_metas[n]

def _DnCn_get_subgroups(n):
    """Add subgroup classes of DnCn (with specific n, except own class)

    The own class (by calling DnC(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n/2, 0, -1) if n % i == 0]
    g = [DnC(i) for i in divs]
    divs.insert(0, n)
    g.extend([C(i) for i in divs])
    return _sort_and_del_dups(g)

class MetaDnCn(type):
    """Meta class for the algebraic group of class DnCn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)

class DnCn(Set):
    """Class for the DnCn symmetry group"""
    __metaclass__ = MetaDnCn
    init_pars = _init_pars('DnCn', 'n')
    std_setup = _std_setup('DnCn', 2)
    order = 0
    n = 0

    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group DnCn, consisting of n rotations and of n rotary
        inversions (reflections)

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n reflections in planes that share the n-fold axis.
        """
        if setup is None:
            setup = {}
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            s = {}
            self.checkSetup(setup)
            if 'n' not in setup:
                if self.n != 0:
                    s['n'] = self.n
                else:
                    s['n'] = copy(self.std_setup['n'])
            else:
                s['n'] = setup['n']
                # If self.n is hard-code (e.g. for D3C3)
                # then if you specify n it should be the correct value
                assert self.n == 0 or s['n'] == self.n
            if 'axis_n' in setup:
                s['axis'] = setup['axis_n']
            else:
                s['axis'] = copy(self.std_setup['axis_n'])
            cn = Cn(setup=s)
            self.direct_parent_setup = copy(s)
            if 'normal_r' in setup:
                s['axis_2'] = setup['normal_r']
            else:
                s['axis_2'] = copy(self.std_setup['normal_r'])
            s['axis_n'] = s['axis']
            del s['axis']
            dn = Dn(setup=s)
            Set.__init__(self, cn | ((dn-cn) * geomtypes.I))
            self.n = s['n']
            self.rot_axes = {'n': cn.rot_axes['n']}
            self.refl_normals = dn.rot_axes[2]
            self.order = dn.order
            self.subgroups = _DnCn_get_subgroups(self.n)
            self.subgroups.insert(0, DnC(self.n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == E:
            return [E()]
        if isinstance(sg, MetaDnCn):
            if sg.n == self.n:
                return [self]
            return [sg(setup={'axis_n': self.rot_axes['n'],
                              'normal_r': self.refl_normals[0]})]
        if isinstance(sg, MetaC2nCn):
            assert sg.n == 1, \
                'Only C2C1 can be subgroup of DnCn (n={})'.format(sg.n)
            # C2C1 ~= E, plus reflection, with normal == rotation axis (0)
            # provide the normal of the one reflection:
            return [sg(setup={'axis': self.refl_normals[0]})]
        if isinstance(sg, MetaCn):
            return [sg(setup={'axis': self.rot_axes['n']})]
        raise ImproperSubgroupError, '{} not subgroup of {}'.format(
            sg.__class__.__name__, self.__class__.__name__)


# dynamically create DnCn classes:
def DnC(n):
    """Create class for DnCn with specific n"""
    try:
        return __DnCn_metas[n]
    except KeyError:
        if n == 1:
            __DnCn_metas[n] = C2C1
        else:
            d_n_c_n = MetaDnCn('D%dC%d' % (n, n), (DnCn,),
                    {
                        'n'    : n,
                        'order': 2 * n,
                        'mixed': True,
                        'directParent': C(n),
                        'init_pars': _init_pars('DnCn', n),
                        'std_setup': _std_setup('DnCn', n)
                    }
                )
            d_n_c_n.subgroups = _DnCn_get_subgroups(n)
            d_n_c_n.subgroups.insert(0, d_n_c_n)
            __DnCn_metas[n] = d_n_c_n
        return __DnCn_metas[n]

def _Dn_get_subgroups(n):
    """Add subgroup classes of Dn (with specific n, except own class)

    The own class (by calling D2nD(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n/2, 0, -1) if n % i == 0]
    g = [D(i) for i in divs]
    divs.insert(0, n)
    g.extend([C(i) for i in divs])
    return _sort_and_del_dups(g)

class MetaDn(type):
    """Meta class for the algebraic group of class Dn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)

class Dn(Set):
    """Class for the Dn symmetry group"""
    __metaclass__ = MetaDn
    init_pars = _init_pars('Dn', 'n')
    std_setup = _std_setup('Dn', 2)
    order = 0
    n = 0
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group Dn, consisting of 2n rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n halfturns around axes perpendicular to the n-fold axis
        """
        if setup is None:
            setup = {}
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            keys = setup.keys()
            if 'axis_n' in keys:
                axis_n = setup['axis_n']
            else:
                axis_n = copy(self.std_setup['axis_n'])
            if 'axis_2' in keys:
                axis_2 = setup['axis_2']
            else:
                axis_2 = copy(self.std_setup['axis_2'])
            if self.n != 0:
                # If self.n is hard-code (e.g. for D3)
                # then if you specify n it should be the correct value
                assert 'n' not in setup or setup['n'] == self.n
                n = self.n
            else:
                if 'n' in keys: n = setup['n']
                else:           n = 2
                if n == 0: n = 1

            h = geomtypes.HalfTurn3(axis=axis_2)
            cn = Cn(setup={'axis': axis_n, 'n': n})
            isometries = [isom for isom in cn]
            hs = [isom * h for isom in cn]
            isometries.extend(hs)
            self.rot_axes = {'n': axis_n, 2: [h.axis() for h in hs]}
            Set.__init__(self, isometries)
            # If self.n is hard-code (e.g. for C3)
            # then if you specify n it should be the correct value
            if self.n != 0:
                assert n == self.n
            else:
                self.n = n
            self.order = 2 * n
            self.subgroups = _Dn_get_subgroups(self.n)
            self.subgroups.insert(0, D(self.n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == E:
            return [E()]
        if isinstance(sg, MetaCn):
            if sg.n == self.n:
                return [sg(setup={'axis': self.rot_axes['n']})]
            if sg.n == 2: # sg = C2
                isoms = [
                    sg(setup={'axis':self.rot_axes[2][i]})
                    for i in range(len(self.rot_axes[2]))
                ]
                if self.n % 2 == 0: # if D2, D4, etc
                    isoms.append(sg(setup={'axis': self.rot_axes['n']}))
                return isoms
            return [sg(setup={'axis': self.rot_axes['n']})]
        if sg.n > self.n:
            return []
        if isinstance(sg, MetaDn):
            if sg.n == self.n:
                return [self]
            return [sg(setup={'axis_n': self.rot_axes['n'],
                              'axis_2': self.rot_axes[2][0]})]


# dynamically create Dn classes:
def D(n):
    """Create class for Dn with specific n"""
    try:
        return __Dn_metas[n]
    except KeyError:
        if n == 1:
            __Dn_metas[n] = C2
        else:
            d_n = MetaDn('D%d' % n, (Dn,),
                    {
                        'n'    : n,
                        'order': 2 * n,
                        'mixed': False,
                        'init_pars': _init_pars('Dn', n),
                        'std_setup': _std_setup('Dn', n)
                    }
                )
            d_n.subgroups = _Dn_get_subgroups(n)
            d_n.subgroups.insert(0, d_n)
            __Dn_metas[n] = d_n
        return __Dn_metas[n]

def _DnxI_get_subgroups(n):
    """Add subgroup classes of DnxI (with specific n, except own class)

    The own class (by calling DxI(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n/2, 0, -1) if n % i == 0]
    # DxI if n odd and divisor odd, or n even and divisor even
    g = [DxI(i) for i in divs if n % 2 == i % 2]
    divs.insert(0, n)
    # CxI if n odd and divisor odd, or n even and divisor even
    g.extend([CxI(i) for i in divs if n % 2 == i % 2])
    # only needed for n even, since
    # if n odd, there are no even divisors
    if n % 2 == 0:
        # since n even: "i % 2 != n % 2" => "i % 2 != 0"
        g.extend([D2nD(i) for i in divs if i % 2 != 0])
        g.extend([C2nC(i) for i in divs if i % 2 != 0])
    g.extend([D(i) for i in divs])
    g.extend([C(i) for i in divs])
    g.extend([DnC(i) for i in divs])
    return _sort_and_del_dups(g)

class MetaDnxI(type):
    """Meta class for the algebraic group of class DnxI"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)

class DnxI(Set):
    """Class for the DnxI symmetry group"""
    __metaclass__ = MetaDnxI
    init_pars = _init_pars('Dn', 'n')
    std_setup = _std_setup('Dn', 2)
    order = 0
    n = 0
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group DnxI, of order 4n.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n halfturns around axes perpendicular to the n-fold axis
        - n rotary inversions around one n-fold axis (angle: i * 2pi/n, with
          0 <= i < n). For n even one of these becomes a reflection in a plane
          perpendicular to the n-fold axis.
        - n reflections in planes that contain the n-fold axis. The normals of
          the reflection planes are perpendicular to the halfturn axes.
        """
        if setup is None:
            setup = {}
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            keys = setup.keys()
            if 'axis_n' in keys: axis_n = setup['axis_n']
            else:                axis_n = copy(self.std_setup['axis_n'])
            self.checkSetup(setup)
            s = copy(setup)
            if 'n' not in s and self.n != 0:
                s['n'] = self.n
            # If self.n is hard-code (e.g. for D3xI)
            # then if you specify n it should be the correct value
            assert self.n == 0 or s['n'] == self.n
            dn = Dn(setup=s)
            self.direct_parent_setup = copy(s)
            Set.__init__(self, dn * ExI())
            self.rot_axes = {'n': dn.rot_axes['n'], 2: dn.rot_axes[2][:]}
            self.n     = dn.n
            self.refl_normals = []
            for isom in self:
                if isom.is_refl():
                    self.refl_normals.append(isom.plane_normal())
            self.order = 2 * dn.order
            self.subgroups = _DnxI_get_subgroups(self.n)
            self.subgroups.insert(0, DxI(self.n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == ExI:
            return [ExI()]
        if sg == E:
            return [E()]
        if sg.n > self.n:
            return []
        if isinstance(sg, MetaDnxI):
            if sg.n == self.n:
                return [self]
            return [sg(setup={'axis_n': self.rot_axes['n'],
                              'axis_2': self.rot_axes[2][0]})]
        if isinstance(sg, (MetaDn, MetaD2nDn)):
            return [
                sg(setup={'axis_n': self.rot_axes['n'],
                          'axis_2': self.rot_axes[2][0]})
                # choosing other 2-fold axes leads essentially to the same.
            ]
        if isinstance(sg, MetaDnCn):
            return [sg(setup={'axis_n':self.rot_axes['n'],
                              'normal_r': self.rot_axes[2][0]})]
        if isinstance(sg, MetaC2nCn):
            if sg.n == 1:
                sg1 = sg(setup={'axis':self.refl_normals[0]})
                if self.n % 2 == 1:
                    return [sg1]
                return [sg1, sg(setup={'axis':self.rot_axes['n']})]
            return [sg(setup={'axis':self.rot_axes['n']})]
        if isinstance(sg, (MetaCn, MetaCnxI)):
            real_std = sg(setup={'axis':self.rot_axes['n']})
            if sg.n == 2:
                # special case: D1xI ~= C2xI or D1 ~= C2
                real_spec = sg(setup={'axis':self.rot_axes[2][0]})
                if self.n % 2 != 0:
                    return [real_spec]
                else:
                    return [real_spec, real_std]
            else:
                return [real_std]
        raise ImproperSubgroupError, '{} not subgroup of {}'.format(
            sg.__name__, self.__class__.__name__)


# dynamically create DnxI classes:
def DxI(n):
    """Create class for DnxI with specific n"""
    assert n != 0
    try:
        return __DnxI_metas[n]
    except KeyError:
        if n == 1:
            __DnxI_metas[n] = C2xI
        else:
            dnxi = MetaDnxI('D%dxI' % n, (DnxI,),
                    {
                        'n'    : n,
                        'order': 4 * n,
                        'mixed': True,
                        'directParent': D(n),
                        'init_pars': _init_pars('Dn', n),
                        'std_setup': _std_setup('Dn', n)
                    }
                )
            dnxi.subgroups = _DnxI_get_subgroups(n)
            dnxi.subgroups.insert(0, dnxi)
            __DnxI_metas[n] = dnxi
        return __DnxI_metas[n]

def _D2nDn_get_subgroups(n):
    """Add subgroup classes of D2nDn (with specific n, except own class)

    The own class (by calling D2nD(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n/2, 0, -1) if n % i == 0]
    # D2nxDn if n odd and divisor odd, or n even and divisor even
    if n % 2 == 0:
        g = [D2nD(i) for i in divs if i % 2 == 0 and (n / i) % 2 == 1]
    else:
        g = [D2nD(i) for i in divs if i % 2 == 1]
    divs.insert(0, n)
    if n % 2 == 0:
        # C2nxCn if n even and divisor even, and n/i odd
        g.extend([C2nC(i) for i in divs if i % 2 == 0 and (n / i) % 2 == 1])
    else:
        # TODO: this ok for all odd?
        # C2nxCn if n odd and divisor odd
        g.extend([C2nC(i) for i in divs if i % 2 == 1])
    # DnxI and CnxI cannot be aligned if i % 2 != n % 2
    g.extend([D(i) for i in divs])
    g.extend([C(i) for i in divs])
    g.extend([DnC(i) for i in divs])
    return _sort_and_del_dups(g)

class MetaD2nDn(type):
    """Meta class for the algebraic group of class D2nDn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)

class D2nDn(Set):
    """Class for the D2nDn symmetry group"""
    __metaclass__ = MetaD2nDn
    init_pars = _init_pars('Dn', 'n')
    std_setup = _std_setup('Dn', 2)
    order = 0
    n = 0
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group D2nDn, consisting of n rotations, n half turns, n
        rotary inversions (reflections) and n reflections.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - n rotations around one n-fold axis (angle: i * 2pi/n, with 0 <= i < n)
        - n halfturns around axes perpendicular to the n-fold axis
        - n rotary inversions around one n-fold axis (angle: pi(1 + 2i)/n, with
          0 <= i < n). For n odd one of these becomes a reflection in a plane
          perpendicular to the n-fold axis.
        - n reflections in planes that contain the n-fold axis. The normal of
          the reflection planes lie in the middle between two halfturns.
        """
        if setup is None:
            setup = {}
        if isometries != None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            s = copy(setup)
            if 'n' not in s and self.n != 0:
                s['n'] = self.n
            # If self.n is hard-code (e.g. for D6D3)
            # then if you specify n it should be the correct value
            assert self.n == 0 or s['n'] == self.n
            dn = Dn(setup=s)
            self.n = dn.n
            s['n'] = 2 * s['n']
            d2n = Dn(setup=s)
            self.direct_parent_setup = copy(s)
            Set.__init__(self, dn | ((d2n-dn) * geomtypes.I))
            self.rot_axes = dn.rot_axes
            self.refl_normals = []
            for isom in self:
                if isom.is_refl():
                    self.refl_normals.append(isom.plane_normal())
            self.order = d2n.order
            self.subgroups = _D2nDn_get_subgroups(self.n)
            self.subgroups.insert(0, D2nD(self.n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == ExI:
            return [ExI()]
        if sg == E:
            return [E()]
        if sg.n > self.n:
            return []
        if isinstance(sg, MetaD2nDn):
            if sg.n == self.n:
                return [self]
            return [sg(setup={'axis_n': self.rot_axes['n'],
                              'axis_2': self.rot_axes[2][0]})]
        if isinstance(sg, MetaDn):
            return [
                sg(setup={'axis_n': self.rot_axes['n'],
                          'axis_2': self.rot_axes[2][0]})
            ]
        if isinstance(sg, MetaDnCn):
            if sg.n == 2 and self.n % 2 != 0:
                return [sg(setup={'axis_n':self.rot_axes[2][0],
                                  'normal_r': self.rot_axes['n']})]
            return [sg(setup={'axis_n':self.rot_axes['n'],
                              'normal_r': self.refl_normals[0]})]
        if isinstance(sg, MetaC2nCn):
            if sg.n == 1:
                sg1 = sg(setup={'axis':self.refl_normals[0]})
                if self.n % 2 == 0:
                    return [sg1]
                return [sg1, sg(setup={'axis':self.rot_axes['n']})]
            return [sg(setup={'axis':self.rot_axes['n']})]
        if isinstance(sg, MetaCn):
            if sg.n == 2:
                sg1 = sg(setup={'axis':self.rot_axes[2][0]})
                if self.n % 2 == 0:
                    return [sg1, sg(setup={'axis': self.rot_axes['n']})]
                return [sg1]
            return [sg(setup={'axis': self.rot_axes['n']})]
        # Note: no DnxI, CnxI subgroups exist, see _D2nDn_get_subgroups
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)


# dynamically create D2nDn classes:
def D2nD(n):
    """Create class for D2nDn with specific n"""
    assert n != 0
    try:
        return __D2nDn_metas[n]
    except KeyError:
        if n == 1:
            # D2D1 ~= D2C2
            __D2nDn_metas[n] = D2C2
        else:
            d_2n_d_n = MetaD2nDn('D%dD%d' % (2*n, n), (D2nDn,),
                    {
                        'n'    : n,
                        'order': 4 * n,
                        'mixed': True,
                        'directParent': D(n),
                        'init_pars': _init_pars('Dn', n),
                        'std_setup': _std_setup('Dn', n)
                    }
                )
            d_2n_d_n.subgroups = _D2nDn_get_subgroups(n)
            d_2n_d_n.subgroups.insert(0, d_2n_d_n)
            __D2nDn_metas[n] = d_2n_d_n
        return __D2nDn_metas[n]

class A4(Set):
    """Class for the A4 symmetry group

    It contains only the direct symmetries of a Tetrahedron.
    """
    init_pars = _init_pars('A4')
    std_setup = _std_setup('A4')
    order = 12
    mixed = False
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group A4, consisting of 12 rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - the identity E, and 3 orthogonal halfturns
        - 8 order 3 isometries.
        The group can be generated by the axes of 2 half turns, but this will
        not generate the group uniquely: There are 2 possibilities: the two
        tetrahedra in a Stella Octagula. The order of the 2 axes of the 2 half
        turns decides which position is obtained.
        """
        if isometries is None and setup is None:
            setup = {}
        # A4 consists of:
        # 1. A subgroup D2: E, and half turns h0, h1, h2
        if isometries != None:
            assert len(isometries) == self.order, "%d != %d" % (
                                                self.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            axes = setup.keys()
            if 'o2axis0' in axes:
                o2axis0 = setup['o2axis0']
            else:
                o2axis0 = copy(self.std_setup['o2axis0'])
            if 'o2axis1' in axes:
                o2axis1 = setup['o2axis1']
            else:
                o2axis1 = copy(self.std_setup['o2axis1'])
            d2 = generate_d2(o2axis0, o2axis1)
            h0, h1, h2 = d2
            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = generate_a4_o3(d2)

            Set.__init__(self, [
                    geomtypes.E,
                    h0, h1, h2,
                    r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2
                ])

            self.rot_axes = {
                    2: [h0.axis(), h1.axis(), h2.axis()],
                    3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()],
                }

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == A4:
            return [self]
        elif sg == D2:
            o2a = self.rot_axes[2]
            return [D2(setup={'axis_n': o2a[0], 'axis_2': o2a[1]})]
        elif sg == C2:
            o2a = self.rot_axes[2]
            return [C2(setup={'axis': a}) for a in o2a]
        elif sg == C3:
            o3a = self.rot_axes[3]
            return [C3(setup={'axis': a}) for a in o3a]
        elif sg == E:
            return [E()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)

class S4A4(Set):
    """Class for the S4A4 symmetry group

    It is the complete symmetry group of a Tetrahedron.
    """
    init_pars = _init_pars('A4')
    std_setup = _std_setup('A4')
    order = 24
    mixed = True
    directParent = A4
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group S4A4, consisting of 24 isometries, 12 direct, 12
        opposite.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
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
        # 1. A subgroup D2: E, and half turns h0, h1, h2
        if isometries is None and setup is None:
            setup = {}
        if isometries != None:
            assert len(isometries) == self.order, "%d != %d" % (
                                                self.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            axes = setup.keys()
            if 'o2axis0' in axes:
                o2axis0 = setup['o2axis0']
            else:
                o2axis0 = copy(self.std_setup['o2axis0'])
            if 'o2axis1' in axes:
                o2axis1 = setup['o2axis1']
            else:
                o2axis1 = copy(self.std_setup['o2axis1'])
            self.direct_parent_setup = copy(setup)
            d2 = generate_d2(o2axis0, o2axis1)
            h0, h1, h2 = d2
            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = generate_a4_o3(d2)

            ax0 = h0.axis()
            ax1 = h1.axis()
            ax2 = h2.axis()
            ri0_1 = geomtypes.RotInv3(axis=ax0, angle=QUARTER_TURN)
            ri0_3 = geomtypes.RotInv3(axis=ax0, angle=3*QUARTER_TURN)
            ri1_1 = geomtypes.RotInv3(axis=ax1, angle=QUARTER_TURN)
            ri1_3 = geomtypes.RotInv3(axis=ax1, angle=3*QUARTER_TURN)
            ri2_1 = geomtypes.RotInv3(axis=ax2, angle=QUARTER_TURN)
            ri2_3 = geomtypes.RotInv3(axis=ax2, angle=3*QUARTER_TURN)
            pn0 = geomtypes.Rot3(axis=ax0, angle=EIGHTH_TURN) * ax1
            pn1 = geomtypes.Rot3(axis=ax0, angle=3*EIGHTH_TURN) * ax1
            pn2 = geomtypes.Rot3(axis=ax1, angle=EIGHTH_TURN) * ax0
            pn3 = geomtypes.Rot3(axis=ax1, angle=3*EIGHTH_TURN) * ax0
            pn4 = geomtypes.Rot3(axis=ax2, angle=EIGHTH_TURN) * ax0
            pn5 = geomtypes.Rot3(axis=ax2, angle=3*EIGHTH_TURN) * ax0
            s0 = geomtypes.Refl3(normal=pn0)
            s1 = geomtypes.Refl3(normal=pn1)
            s2 = geomtypes.Refl3(normal=pn2)
            s3 = geomtypes.Refl3(normal=pn3)
            s4 = geomtypes.Refl3(normal=pn4)
            s5 = geomtypes.Refl3(normal=pn5)
            Set.__init__(self, [
                    geomtypes.E,
                    h0, h1, h2,
                    r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2,
                    s0, s1, s2, s3, s4, s5,
                    ri0_1, ri0_3, ri1_1, ri1_3, ri2_1, ri2_3,
                ])

            self.refl_normals = [pn0, pn1, pn2, pn3, pn4, pn5]
            self.rot_axes = {
                    2: [h0.axis(), h1.axis(), h2.axis()],
                    3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()],
                }

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        #S4A4, A4, D2nDn, DnCn, C2nCn, Dn, Cn
        #C3, C2, E
        if sg == S4A4:
            return [self]
        elif sg == A4:
            o2a = self.rot_axes[2]
            return [sg(setup={'o2axis0': o2a[0], 'o2axis1': o2a[1]})]
        elif sg == D4D2:
            o2a = self.rot_axes[2]
            l = len(o2a)
            return [sg(setup={'axis_n': o2a[i], 'axis_2': o2a[(i+1)%l]})
                    for i in range(l)
                ]
        elif sg == D3C3:
            isoms = []
            for o3 in self.rot_axes[3]:
                for rn in self.refl_normals:
                    if geomtypes.eq(rn*o3, 0):
                        isoms.append(sg(setup={'axis_n': o3, 'normal_r': rn}))
                        break
            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
            return isoms
        elif sg == C4C2:
            return [C4C2(setup={'axis': a}) for a in self.rot_axes[2]]
        elif sg == C3:
            return [sg(setup={'axis': a}) for a in self.rot_axes[3]]
        elif sg == C2:
            return [sg(setup={'axis': a}) for a in self.rot_axes[2]]
        elif sg == C2C1:
            return [sg(setup={'axis': normal}) for normal in self.refl_normals]
        elif sg == E:
            return [E()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)

class A4xI(Set):
    """Class for the A4xI symmetry group

    It contains the direct symmetries of a Tetrahedron combined with the
    central inversion.
    """
    init_pars = _init_pars('A4')
    std_setup = _std_setup('A4')
    order = 24
    mixed = True
    directParent = A4
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group A4xI, consisting of 12 rotations and 12 rotary
        inversions.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - the identity E, and 3 orthogonal halfturns
        - 8 order 3 rotations.
        - the central inversion I, 3 reflections
        - 8 order rotary inversions
        The group can be generated by the axes of 2 half turns
        """
        if isometries is None and setup is None:
            setup = {}
        if isometries != None:
            assert len(isometries) == self.order, "%d != %d" % (
                                                self.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            a4 = A4(setup=setup)
            self.direct_parent_setup = copy(setup)
            Set.__init__(self, a4 * ExI())
            self.rot_axes = a4.rot_axes

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == A4xI:
            return [self]
        elif sg == A4:
            # other ways of orienting A4 into A4xI don't give anything new
            return [ A4( setup = {
                        'o2axis0': self.rot_axes[2][0],
                        'o2axis1': self.rot_axes[2][1]
                    }
                )
            ]
        elif sg == D2xI:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis_n': o2a[0], 'axis_2': o2a[1]})]
        elif sg == C3xI:
            o3a = self.rot_axes[3]
            return [sg(setup={'axis': a}) for a in o3a]
        elif sg == D2:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis_n': o2a[0], 'axis_2': o2a[1]})]
        elif sg == D2C2:
            isoms = []
            for o2 in self.rot_axes[2]:
                for rn in self.rot_axes[2]:
                    if geomtypes.eq(rn*o2, 0):
                        isoms.append(sg(setup={'axis_n': o2, 'normal_r': rn}))
                        break
            assert len(isoms) == 3, 'len(isoms) == %d != 3' % len(isoms)
            return isoms
        if sg == C2xI:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis': a}) for a in o2a]
        elif sg == C3:
            o3a = self.rot_axes[3]
            return [sg(setup={'axis': a}) for a in o3a]
        elif sg == C2:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis': a}) for a in o2a]
        elif sg == C2C1:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis': a}) for a in o2a]
        elif sg == ExI:
            return [sg()]
        elif sg == E:
            return [sg()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)

class S4(Set):
    """Class for the S4 symmetry group

    This is the symmetry group of the cube or octahedron with only the direct
    symmetries.
    """
    init_pars = _init_pars('S4')
    std_setup = _std_setup('S4')
    order = 24
    mixed = False
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group S4, consisting of 24 rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - the identity E,
        - and 9 orthogonal turns based on quarter turns (1/4, 1/2, 3/4)
        - 8 turns based on third turns (1/3, 2/3).
        - 6 halfturns
        The group can be generated by the axes of 2 quarter turns,
        """
        if isometries is None and setup is None:
            setup = {}
        if isometries != None:
            assert len(isometries) == self.order, "%d != %d" % (
                                                self.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            axes = setup.keys()
            if 'o4axis0' in axes:
                o4axis0 = setup['o4axis0']
            else:
                o4axis0 = copy(self.std_setup['o4axis0'])
            if 'o4axis1' in axes:
                o4axis1 = setup['o4axis1']
            else:
                o4axis1 = copy(self.std_setup['o4axis1'])
            d2 = generate_d2(o4axis0, o4axis1)
            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = generate_a4_o3(d2)
            q0_2, q1_2, q2_2 = d2
            ax0 = q0_2.axis()
            ax1 = q1_2.axis()
            ax2 = q2_2.axis()
            q0_1 = geomtypes.Rot3(axis=ax0, angle=QUARTER_TURN)
            q0_3 = geomtypes.Rot3(axis=ax0, angle=3*QUARTER_TURN)
            q1_1 = geomtypes.Rot3(axis=ax1, angle=QUARTER_TURN)
            q1_3 = geomtypes.Rot3(axis=ax1, angle=3*QUARTER_TURN)
            q2_1 = geomtypes.Rot3(axis=ax2, angle=QUARTER_TURN)
            q2_3 = geomtypes.Rot3(axis=ax2, angle=3*QUARTER_TURN)
            h0 = geomtypes.Rot3(
                    axis=geomtypes.Rot3(axis=ax0, angle=EIGHTH_TURN) * ax1,
                    angle=HALFTURN
                )
            h1 = geomtypes.Rot3(
                    axis=geomtypes.Rot3(axis=ax0, angle=3*EIGHTH_TURN) * ax1,
                    angle=HALFTURN
                )
            h2 = geomtypes.Rot3(
                    axis=geomtypes.Rot3(axis=ax1, angle=EIGHTH_TURN) * ax0,
                    angle=HALFTURN
                )
            h3 = geomtypes.Rot3(
                    axis=geomtypes.Rot3(axis=ax1, angle=3*EIGHTH_TURN) * ax0,
                    angle=HALFTURN
                )
            h4 = geomtypes.Rot3(
                    axis=geomtypes.Rot3(axis=ax2, angle=EIGHTH_TURN) * ax0,
                    angle=HALFTURN
                )
            h5 = geomtypes.Rot3(
                    axis=geomtypes.Rot3(axis=ax2, angle=3*EIGHTH_TURN) * ax0,
                    angle=HALFTURN
                )
            Set.__init__(self, [
                    geomtypes.E,
                    q0_1, q0_2, q0_3, q1_1, q1_2, q1_3, q2_1, q2_2, q2_3,
                    r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2,
                    h0, h1, h2, h3, h4, h5
                ])
            self.rot_axes = {
                    2: [h0.axis(), h1.axis(), h2.axis(),
                            h3.axis(), h4.axis(), h5.axis()
                        ],
                    3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()],
                    4: [ax0, ax1, ax2]
                }

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == S4:
            return [self]
        elif sg == A4:
            # other ways of orienting A4 into S4 don't give anything new
            return [
                A4(
                    setup = {
                        'o2axis0': self.rot_axes[4][0],
                        'o2axis1': self.rot_axes[4][1]
                    }
                )
            ]
        elif sg == D4:
            o4a = self.rot_axes[4]
            l = len(o4a)
            return [sg(
                    setup = {'axis_n': o4a[i], 'axis_2': o4a[(i+1)%l]}
                ) for i in range(l)
            ]
        elif sg == D3:
            isoms = []
            for o3 in self.rot_axes[3]:
                for o2 in self.rot_axes[2]:
                    if geomtypes.eq(o2*o3, 0):
                        isoms.append(sg(setup={'axis_n': o3, 'axis_2': o2}))
                        break
            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
            return isoms
        elif sg == D2:
            isoms = []
            # There are 2 kinds of D2:
            # 1. one consisting of the three 4-fold axes
            # 2. 3 consisting of a 4 fold axis and two 2-fold axes.
            o4a = self.rot_axes[4]
            l = len(o4a)
            isoms = [sg(setup={'axis_n': o4a[0], 'axis_2': o4a[1]})]
            for o4 in self.rot_axes[4]:
                for o2 in self.rot_axes[2]:
                    if geomtypes.eq(o2*o4, 0):
                        isoms.append(sg(setup={'axis_n': o4, 'axis_2': o2}))
                        break
            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
            return isoms
        elif sg == C4:
            o4a = self.rot_axes[4]
            return [sg(setup={'axis': a}) for a in o4a]
        elif sg == C3:
            o3a = self.rot_axes[3]
            return [sg(setup={'axis': a}) for a in o3a]
        elif sg == C2:
            o4a = self.rot_axes[4]
            isoms = [sg(setup={'axis': a}) for a in o4a]
            o2a = self.rot_axes[2]
            isoms.extend([sg(setup={'axis': a}) for a in o2a])
            return isoms
        elif sg == E:
            return [E()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)

class S4xI(Set):
    """Class for the S4xI symmetry group

    This is the complete symmetry group of the cube or octahedron.
    """
    init_pars = _init_pars('S4')
    std_setup = _std_setup('S4')
    order = 48
    mixed = True
    directParent = S4
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group S4xI, consisting of 12 rotations and 12 rotary
        inversions.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - the identity E,
        - and 9 orthogonal turns based on quarter turns (1/4, 1/2, 3/4)
        - 8 turns based on third turns (1/3, 2/3).
        - 6 halfturns
        - the central inversion I
        - 6 rotary inversions, derived from the 6 quarter turns.
        - 8 rotary inversions, derived from the 8 third turns.
        - 9 reflections, of which 6 are based on (ie orthogonal to) the 2 fold
          axes and 3 on the 4-fold axes.
        The group can be generated by the axes of 2 quarter turns,
        """
        if isometries is None and setup is None:
            setup = {}
        if isometries != None:
            assert len(isometries) == self.order, "%d != %d" % (
                                                self.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            s4 = S4(setup=setup)
            self.direct_parent_setup = copy(setup)
            Set.__init__(self, s4 * ExI())
            self.rot_axes = s4.rot_axes

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == S4xI:
            return [self]
        elif sg == S4:
            # other ways of orienting S4 into S4xI don't give anything new
            return [ sg( setup = {
                        'o4axis0': self.rot_axes[4][0],
                        'o4axis1': self.rot_axes[4][1]
                    }
                )
            ]
        elif sg == A4xI or sg == A4 or sg == S4A4:
            return [ sg( setup = {
                        'o2axis0': self.rot_axes[4][0],
                        'o2axis1': self.rot_axes[4][1]
                    }
                )
            ]
        elif sg == D4xI or sg == D8D4 or sg == D4:
            o4a = self.rot_axes[4]
            l = len(o4a)
            return [sg(
                    setup = {'axis_n': o4a[i], 'axis_2': o4a[(i+1)%l]}
                ) for i in range(l)
            ]
        elif sg == D3xI or sg == D3:
            isoms = []
            for o3 in self.rot_axes[3]:
                for o2 in self.rot_axes[2]:
                    if geomtypes.eq(o2*o3, 0):
                        isoms.append(sg(setup={'axis_n': o3, 'axis_2': o2}))
                        break
            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
            return isoms
        elif sg == D4C4:
            isoms = []
            for a4 in self.rot_axes[4]:
                for rn in self.rot_axes[2]:
                    if geomtypes.eq(rn*a4, 0):
                        isoms.append(sg(setup={'axis_n': a4, 'normal_r': rn}))
                        break
            return isoms
        elif sg == D4D2:
            o4a = self.rot_axes[4]
            l = len(o4a)
            isoms = [sg(setup={'axis_n': o4a[i], 'axis_2': o4a[(i+1)%l]})
                    for i in range(l)
                ]
            o2a = self.rot_axes[2]
            for a4 in o4a:
                for a2 in o2a:
                    if geomtypes.eq(a2*a4, 0):
                        isoms.append(sg(setup={'axis_n': a4, 'axis_2': a2}))
                        break
            return isoms
        elif sg == D2xI or sg == D2:
            o4a = self.rot_axes[4]
            isoms = [sg(setup={'axis_n': o4a[0], 'axis_2': o4a[1]})]
            o2a = self.rot_axes[2]
            for a4 in o4a:
                for a2 in o2a:
                    if geomtypes.eq(a2*a4, 0):
                        isoms.append(sg(setup={'axis_n': a4, 'axis_2': a2}))
                        break
            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
            return isoms
        elif sg == D3C3:
            isoms = []
            for o3 in self.rot_axes[3]:
                for rn in self.rot_axes[2]:
                    if geomtypes.eq(rn*o3, 0):
                        isoms.append(sg(setup={'axis_n': o3, 'normal_r': rn}))
                        break
            assert len(isoms) == 4, 'len(isoms) == %d != 4' % len(isoms)
            return isoms
        elif sg == C3xI or sg == C3:
            o3a = self.rot_axes[3]
            return [sg(setup={'axis': a}) for a in o3a]
        elif sg == D2C2:
            o4a = self.rot_axes[4]
            l = len(o4a)
            isoms = [sg(setup={'axis_n': o4a[i], 'normal_r': o4a[(i+1)%l]})
                    for i in range(l)
                ]
            o2a = self.rot_axes[2]
            for a4 in o4a:
                for a2 in o2a:
                    if geomtypes.eq(a2*a4, 0):
                        isoms.append(sg(setup={'axis_n': a4, 'normal_r': a2}))
                        break
            for o2 in self.rot_axes[2]:
                for rn in self.rot_axes[4]:
                    if geomtypes.eq(rn*o2, 0):
                        isoms.append(sg(setup={'axis_n': o2, 'normal_r': rn}))
                        break
            assert len(isoms) == 12, 'len(isoms) == %d != 12' % len(isoms)
            return isoms
        elif sg == C4xI or sg == C4 or sg == C4C2:
            o4a = self.rot_axes[4]
            return [sg(setup={'axis': a}) for a in o4a]
        elif sg == C2xI or sg == D1xI or sg == C2 or sg == D1:
            o2a = self.rot_axes[4]
            o2a.extend(self.rot_axes[2])
            return [sg(setup={'axis': a}) for a in o2a]
        elif sg == C2C1:
            isoms = [sg(setup={'axis': a}) for a in self.rot_axes[2]]
            isoms.extend([sg(setup={'axis': a}) for a in self.rot_axes[4]])
            return isoms
        elif sg == ExI:
            return [sg()]
        elif sg == E:
            return [sg()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)

def generate_d2(o2axis0, o2axis1):
    """
    Returns 3 orthogonal halfturns for D2
    """
    # if axes is specified as a transform:
    if isinstance(o2axis0, geomtypes.Transform3):
        o2axis0 = o2axis0.axis()
    if isinstance(o2axis1, geomtypes.Transform3):
        o2axis1 = o2axis1.axis()
    assert geomtypes.eq(geomtypes.Vec3(o2axis0) * geomtypes.Vec3(o2axis1), 0), (
            "Error: axes not orthogonal")
    h0 = geomtypes.HalfTurn3(axis=o2axis0)
    h1 = geomtypes.Rot3(axis=o2axis1, angle=HALFTURN)
    return (h0, h1, h1 * h0)

def generate_a4_o3(d2_half_turns):
    """
    Return all order 3 rotations from A4 except E

    d2_half_turns: tuple containing h0, h1, h2
    Return a tuple (r1_1_3, r1_2_3, r2_1_3, r2_2_3, r3_1_3, r3_2_3, r4_1_3,
    r4_2_3)
    """
    h0, h1, h2 = d2_half_turns

    # the one order 3 rotation axis, is obtained as follows:
    # imagine A4 is part of S4 positioned in a cube
    # h0, h1, h2 go through the cube face centres
    # define a quarter turn around h2
    q = geomtypes.Rot3(axis=h2.axis(), angle=QUARTER_TURN)
    # cube_h0 and cube_h1 go through cube edge centres
    cube_h0 = q * h0
    cube_h1 = q * h1
    # o3axis goes through 1 of the 2 cube vertices that form the edge
    # between the faces which centres are on h0 and h1
    o3axis = geomtypes.Rot3(
            axis=cube_h0.axis(), angle=asin_1_V3
        ) * cube_h1.axis()
    # r1_1_3: 1/3 rotation around the first order 3 axis
    # r1_2_3: 2/3 rotation around the first order 3 axis
    r1_1_3 = geomtypes.Rot3(axis=o3axis, angle=THIRD_TURN)
    r1_2_3 = geomtypes.Rot3(axis=o3axis, angle=2*THIRD_TURN)
    r4_1_3 = r1_1_3 * h0
    r3_1_3 = r1_1_3 * h1
    r2_1_3 = r1_1_3 * h2
    r2_2_3 = r1_2_3 * h0
    r4_2_3 = r1_2_3 * h1
    r3_2_3 = r1_2_3 * h2
    return (r1_1_3, r1_2_3, r2_1_3, r2_2_3, r3_1_3, r3_2_3, r4_1_3, r4_2_3)

class A5(Set):
    """Class for the A5 symmetry group

    This contain only the direct symmetries of the icosaheron or dodecahedron
    """
    init_pars = _init_pars('A5')
    std_setup = _std_setup('A5')
    order = 60
    mixed = False
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group A5, consisting of 60 rotations

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - the identity E,
        - 24 turns based on the  6  5-fold turns (1/5, 2/5, 3/5, 4/5)
        - 20 turns based on the 10  3-fold turns (1/3, 2/3)
        - 15 halfturns
        The group can be generated by the axes of 2 quarter turns,
        """
        if isometries is None and setup is None:
            setup = {}
        if isometries != None:
            assert len(isometries) == self.order, "%d != %d" % (
                                                self.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            axes = setup.keys()
            if 'o3axis' in axes:
                o3axis = setup['o3axis']
            else: o3axis = copy(self.std_setup['o3axis'])
            if 'o5axis' in axes:
                o5axis = setup['o5axis']
            else: o5axis = copy(self.std_setup['o5axis'])

            turn5 = 2 * math.pi / 5
            turn3 = 2 * math.pi / 3
            r0_1_5 = geomtypes.Rot3(axis=o5axis, angle=turn5)
            r0_1_3 = geomtypes.Rot3(axis=o3axis, angle=turn3)
            o3axes = [o3axis]                           # o3[0]
            o5axes = [r0_1_3 * o5axis]                  # o5[0]
            for i in range(4):
                o3axes.append(r0_1_5 * o3axes[-1])      # o3[1:5]
                o5axes.append(r0_1_5 * o5axes[-1])      # o5[1:5]
            o5axes.append(o5axis)                       # o5[5] ... done
            o2axes = [(o5axis + o5axes[i]) / 2
                      for i in range(5)]                # o2[0:5]
            o2axes.extend([(o5axes[i] + o5axes[(i+4) % 5]) / 2
                           for i in range(5)])          # o2[5:10]
            o3axes.extend([geomtypes.HalfTurn3(axis=o2axes[i+5]) * o3axes[i]
                           for i in range(5)])          # o3[5:10] ... done
            o2axes.extend([geomtypes.HalfTurn3(axis=o2axes[i])
                           * o2axes[(i+2) % 5]
                           for i in range(5)])          # o2[10:15] ... done
            transforms = [geomtypes.E]
            for a in o5axes:
                transforms.extend([geomtypes.Rot3(axis=a, angle=i * turn5)
                                   for i in range(1, 5)])
            for a in o3axes:
                transforms.extend([geomtypes.Rot3(axis=a, angle=i * turn3)
                                   for i in range(1, 3)])

#        ___---.__
#      .L     / \_""__
#     /  \ _14 9  \   "\
#  10/ 5  4----9___|_13-.
#   /  5/  \  4    3  8 |
#   |/"  0  4   3-" \  /
#   0__     \_-"  3  8 |
#   \  "0--_5__       \/
#    \      |  ""2--__2
#     \_ 1  1   2  _.-" <--- o2_e12
#    _ 6\_   |  _7" __
#    /|   "-_1-"    |\
#   6     ^           7
#         |
#       o2_11

            transforms.extend([geomtypes.HalfTurn3(axis=a) for a in o2axes])
            Set.__init__(self, transforms)
            self.rot_axes = { 2: o2axes, 3: o3axes, 5: o5axes }

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == A5:
            return [self]
        if sg == A4:
            return [
                # Essentially these lead to 3 different colourings, of which 2
                # pairs are mirrors images.
                sg(setup={'o2axis0': self.rot_axes[2][i],
                          'o2axis1': self.rot_axes[2][((i+3) % 5) + 5]})
                for i in range(5)
            ]
        if sg == D5:
            isoms = [sg(setup={'axis_n': self.rot_axes[5][i],
                               'axis_2': self.rot_axes[2][(i+2) % 5]})
                     for i in range(5)]
            isoms.append(
                sg(setup={'axis_n': self.rot_axes[5][5],
                          'axis_2': self.rot_axes[2][10]})
            )
            return isoms
        if sg == D3:
            isoms = [sg(setup={'axis_n': self.rot_axes[3][i],
                               'axis_2': self.rot_axes[2][((i+3) % 5) + 5]})
                     for i in range(5)]
            isoms.extend([sg(setup={'axis_n': self.rot_axes[3][i + 5],
                                    'axis_2': self.rot_axes[2][(i+3) % 5]})
                          for i in range(5)])
            return isoms
        if sg == D2:
            return [sg(setup={'axis_n': self.rot_axes[2][i],
                              'axis_2': self.rot_axes[2][((i+3) % 5) + 5]})
                    for i in range(5)]
        if sg == C5:
            return [sg(setup={'axis': a}) for a in self.rot_axes[5]]
        if sg == C3:
            return [sg(setup={'axis': a}) for a in self.rot_axes[3]]
        if sg == C2:
            return [sg(setup={'axis': a}) for a in self.rot_axes[2]]
        if sg == E:
            return [sg()]
        else:
            raise ImproperSubgroupError, '{} not subgroup of {}'.format(
                sg.__class__.__name__, self.__class__.__name__)

class A5xI(Set):
    """Class for the A5xI symmetry group

    This is the complete symmetry group of the icosaheron or dodecahedron
    """
    init_pars = _init_pars('A5')
    std_setup = _std_setup('A5')
    order = 120
    mixed = True
    directParent = A5
    def __init__(self, isometries=None, setup=None):
        """
        The algebraic group A5xI, which is the complete symmetry of an
        icosahedron, It consists of 120 isometries.

        either provide the complete set or provide setup that generates
        the complete group. For the latter see the class init_pars argument.
        Contains:
        - the identity E,
        - 24 turns based on the  6  5-fold turns (1/5, 2/5, 3/5, 4/5)
        - 20 turns based on the 10  3-fold turns (1/3, 2/3)
        - 15 halfturns
        - the central inversion I
        - 24 rotary inversions based on the  6  5-fold axes (1/5, 2/5, 3/5, 4/5)
        - 20 rotary inversions based on the 10  3-fold axes (1/3, 2/3)
        - 15 reflections
        """
        if isometries is None and setup is None:
            setup = {}
        if isometries != None:
            assert len(isometries) == self.order, "%d != %d" % (
                                                self.order, len(isometries))
            # TODO: more asserts?
            Set.__init__(self, isometries)
        else:
            self.checkSetup(setup)
            a5 = A5(setup=setup)
            self.direct_parent_setup = copy(setup)
            Set.__init__(self, a5 * ExI())
            self.rot_axes = a5.rot_axes

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == A5xI:
            return [self]
        if sg == A5:
            # other ways of orienting A5 into A5xI don't give anything new
            return [sg( setup = {'o3axis': self.rot_axes[3][0],
                                 'o5axis': self.rot_axes[5][0]})]
        if sg == A4xI or sg == A4:
            return [
                # Essentially these lead to 3 different colourings, of which 2
                # pairs are mirrors images. For A4xI the mirrors should lead to
                # to equal solutions.
                sg(setup={'o2axis0': self.rot_axes[2][i],
                          'o2axis1': self.rot_axes[2][((i+3) % 5) + 5]})
                for i in range(5)
            ]
        if sg == D5xI or sg == D5:
            isoms = [sg(setup={'axis_n': self.rot_axes[5][i],
                               'axis_2': self.rot_axes[2][(i+2) % 5]})
                     for i in range(5)]
            isoms.append(sg(setup={'axis_n': self.rot_axes[5][5],
                                   'axis_2': self.rot_axes[2][10]}))
            return isoms
        if sg == D5C5:
            isoms = [sg(setup={'axis_n': self.rot_axes[5][i],
                               'normal_r': self.rot_axes[2][(i+2) % 5]})
                     for i in range(5)]
            isoms.append(sg(setup={'axis_n': self.rot_axes[5][5],
                                   'normal_r': self.rot_axes[2][10]}))
            return isoms
        if sg == D3xI or sg == D3:
            isoms = [sg(setup={'axis_n': self.rot_axes[3][i],
                               'axis_2': self.rot_axes[2][((i+3) % 5) + 5]})
                     for i in range(5)]
            isoms.extend([sg(setup={'axis_n': self.rot_axes[3][i + 5],
                                    'axis_2': self.rot_axes[2][(i+3) % 5]})
                          for i in range(5)])
            return isoms
        if sg == D3C3:
            isoms = [sg(setup={'axis_n': self.rot_axes[3][i],
                               'normal_r': self.rot_axes[2][((i+3) % 5) + 5]})
                     for i in range(5)]
            isoms.extend([sg(setup={'axis_n': self.rot_axes[3][i + 5],
                                    'normal_r': self.rot_axes[2][(i+3) % 5]})
                          for i in range(5)])
            return isoms
        if sg == D2xI or sg == D2:
            return [sg(setup={'axis_n': self.rot_axes[2][i],
                              'axis_2': self.rot_axes[2][((i+3) % 5) + 5]})
                    for i in range(5)]
        if sg == D2C2:
            return [sg(setup={'axis_n': self.rot_axes[2][i],
                              'normal_r': self.rot_axes[2][((i+3) % 5) + 5]})
                    for i in range(5)]
        if sg == C5xI or sg == C5:
            return [sg(setup={'axis': a}) for a in self.rot_axes[5]]
        if sg == C3xI or sg == C3:
            return [sg(setup={'axis': a}) for a in self.rot_axes[3]]
        if sg == C2xI or sg == C2 or sg == C2C1 or sg == D1xI or sg == D1:
            return [sg(setup={'axis': a}) for a in self.rot_axes[2]]
        if sg == ExI:
            return [sg()]
        if sg == E:
            return [sg()]
        raise ImproperSubgroupError, '{} not subgroup of {}'.format(
            sg.__class__.__name__, self.__class__.__name__)

C1 = E
C2 = C(2)
C3 = C(3)
C4 = C(4)
C5 = C(5)

C1xI = ExI
C2xI = CxI(2)
C3xI = CxI(3)
C4xI = CxI(4)
C5xI = CxI(5)

C2C1 = C2nC(1)
C4C2 = C2nC(2)
C6C3 = C2nC(3)
C8C4 = C2nC(4)

D1C1 = DnC(1)
D2C2 = DnC(2)
D3C3 = DnC(3)
D4C4 = DnC(4)
D5C5 = DnC(5)

D1 = D(1)
D2 = D(2)
D3 = D(3)
D4 = D(4)
D5 = D(5)

D1xI = DxI(1)
D2xI = DxI(2)
D3xI = DxI(3)
D4xI = DxI(4)
D5xI = DxI(5)

D2D1 = D2nD(1)
D4D2 = D2nD(2)
D6D3 = D2nD(3)
D8D4 = D2nD(4)

# Dn = D2, (D1~C2)
# Cn = C3, C2
A4.subgroups = [A4, D2, C3, C2, E]

# Diagram 4, 14
# 24            A4xI
#            _.-'| |'-._
#         .-'    | |    '-._
# 12     A4      |  \       '-.._
#         |\     |   |           '-._
#  8      | |    |   |               D2xI
#         | \    |    \         ____/ |
#  6      |  |  C3xI   |   to D2      |
#         |  \   /\    |              |
#  4     D2   | /  | D2C2      __----C2xI
#         |   \/  to   |  to C2  _.--'|
#  3      |   C3  ExI  |     _.-'     |
#         |   |        | _.-'         |
#  2     C2   |      C2C1          __ExI
#         '-._|__..--' ____....''''
#  1          E----''''
A4xI.subgroups = [A4xI, A4,
                  D2xI, C3xI,
                  D2, D2C2, C2xI,
                  C3,
                  C2, C2C1, ExI, E]

# Dn = D2, (D1~C2)
# Cn = C3, C2
# D2nDn = D4D2
# DnCn  = D3C3, D2C2
# C2nCn = C4C2, C2C1
# Diagram 1.
S4A4.subgroups = [S4A4,
                  A4, D4D2, D3C3,
                  C4C2,
                  C3,
                  C2C1, C2,
                  E]

# Dn = D4, D3, D2 (2x), D1 (~C2)
# Cn = C4, C3, C2 (2x @ 2-fold and 4-fold axes)
S4.subgroups = [S4, A4,
                D4, D3,
                D2, C4,
                C3,
                C2,
                E]

S4xI.subgroups = [S4xI,                        # 48
                  S4, S4A4, A4xI,              # 24
                  D4xI,                        # 18
                  A4, D3xI,                    # 12
                  D4D2, D2xI, D4, C4xI, D4C4,  #  8
                  D3, D3C3, C3xI,              #  6
                  D2, D2C2, C2xI, C4, C4C2,    #  4
                  C3,                          #  3
                  C2, C2C1, ExI,               #  2
                  E]

# Diagram 15
A5.subgroups = [A5,
                A4,  # 12
                D5,  # 10
                D3,  #  6
                C5,  #  5
                D2,  #  4
                C3,  #  3
                C2,  #  2
                E]

A5xI.subgroups = [A5xI,            # 120
                  A5,              #  60
                  A4xI,            #  24
                  D5xI,            #  20
                  A4, D3xI,        #  12
                  D5, D5C5, C5xI,  #  10
                  D3, D3C3, C3xI,  #   6
                  C5,              #   5
                  D2, D2C2, C2xI,  #   4
                  C3,              #   3
                  C2, C2C1, ExI,   #   2
                  E]

Cn.subgroups = [Cn, E]
CnxI.subgroups = [CnxI, Cn, ExI, E]
C2nCn.subgroups = [C2nCn, Cn, E]
DnCn.subgroups = [DnCn, Cn, E]
Dn.subgroups = [Dn, Cn, C2, E]
DnxI.subgroups = [DnxI, Dn, CnxI, Cn, C2xI, C2, ExI, E]
D2nDn.subgroups = [D2nDn, Dn, C2nCn, Cn, E]
