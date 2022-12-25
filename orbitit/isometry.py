#!/usr/bin/env python
"""Module that contains classes for symmetry groups using group algebra."""
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
# pylint: disable=too-many-lines,too-many-return-statements,too-many-branches
# pylint: disable=too-many-locals,too-many-statements


from copy import copy, deepcopy
import logging
import math

from orbitit import base, geomtypes, indent

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
        {'type': 'vec3', 'par': 'o2axis1',
         'lab': "half turn of orthogonal axis"}
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

def ensure_axis_type(axis):
    """Return an 3D axis using the right type."""
    if not isinstance(axis, geomtypes.Vec3):
        if isinstance(axis, list):
            axis = geomtypes.Vec3(axis)
        else:
            raise TypeError
    return axis


HALFTURN = geomtypes.HALF_TURN
QUARTER_TURN = geomtypes.QUARTER_TURN
EIGHTH_TURN = QUARTER_TURN / 2
THIRD_TURN = geomtypes.THIRD_TURN

ASIN_1_V3 = math.asin(1.0 / math.sqrt(3))

I = geomtypes.I  # central inversion

__Cn_metas = {}
__C2nCn_metas = {}
__CnxI_metas = {}
__DnCn_metas = {}
__Dn_metas = {}
__DnxI_metas = {}
__D2nDn_metas = {}


def a5_sub_a4_setup(rot_axes):
    """Return all orientation set-ups for subgroup A4 for certain A5 rot_axes"""
    setup = []
    look_for_no = 0
    for n, axis1 in enumerate(rot_axes[2]):
        for axis2 in rot_axes[2][n + 1:]:
            if geomtypes.eq(axis1 * axis2, 0):
                setup.append({'o2axis0': axis1, 'o2axis1': axis2})
                look_for_no += 1
                break
        if look_for_no >= 5:  # there are 5 A4 in A5
            break
    return setup


def a5_sub_d5_setup(rot_axes):
    """Return all orientation set-ups for subgroup D5 for certain A5 rot_axes"""
    setup = []
    for _, axis1 in enumerate(rot_axes[5]):
        for axis2 in rot_axes[2]:
            if geomtypes.eq(axis1 * axis2, 0):
                setup.append({'axis_n': axis1, 'axis_2': axis2})
                break
    return setup


def a5_sub_d3_setup(rot_axes):
    """Return all orientation set-ups for subgroup D3 for certain A5 rot_axes"""
    setup = []
    for _, axis1 in enumerate(rot_axes[3]):
        for axis2 in rot_axes[2]:
            if geomtypes.eq(axis1 * axis2, 0):
                setup.append({'axis_n': axis1, 'axis_2': axis2})
                break
    return setup


def a5_get_std_subgroup_setups(rot_axes):
    """Define the subgroup setup parameter for the standard A5 position."""
    _sub_a4_setup = [{'o2axis0': rot_axes[2][i],
                      'o2axis1': rot_axes[2][((i+3) % 5) + 5]}
                     for i in range(5)]
    _sub_d5_setup = [{'axis_n': rot_axes[5][i],
                      'axis_2': rot_axes[2][(i+2) % 5]}
                     for i in range(5)]
    _sub_d5_setup.append({'axis_n': rot_axes[5][5],
                          'axis_2': rot_axes[2][10]})
    _sub_d3_setup = [{'axis_n': rot_axes[3][i],
                      'axis_2': rot_axes[2][((i+3) % 5) + 5]}
                     for i in range(5)]
    _sub_d3_setup.extend([{'axis_n': rot_axes[3][i + 5],
                           'axis_2': rot_axes[2][(i+3) % 5]}
                          for i in range(5)])
    # D2 is Similar to A4 (D2 is subgroup of A4), no need to set here.
    # D3C3 is Similar to D3, no need to set here.
    # D2C2 is Similar to D2, no need to set here.
    return _sub_a4_setup, _sub_d5_setup, _sub_d3_setup


def _sort_and_del_dups(g):
    """Sort list of isometry classes and remove duplicates"""
    # remove duplicates first (unsorts the list):
    g = list(dict.fromkeys(g))
    g.sort(key=lambda x: x.order, reverse=True)
    return g


def _get_alternative_subgroups(sg, pars, chk, realise):
    """Generate alternative subgroup realisations for sg in g

    sg: class of subgroup to be realised (instantiated)
    pars: list of possible parameters in the setup for sg realisation
    chk: function to check whether a sg object already is added. The parameters
         of this function is (g, p), where g is a subgroup object and p is the
         parameter from pars that is being checked.
    realise: function to call to instantiate sg with a p in the setup
    """
    result = []
    for p in pars:
        add = True
        for r in result:
            if chk(r, p):
                add = False
                break
        if add:
            result.append(realise(sg, p))
    return result


def get_axes(transforms, n=0):
    """From an list of transforms get all n-fold axes.

    isoms: list/tuple of transforms
    n: integer expressing amount of rotation in full turn, if nothing
       specified, then any n-fold axis is ok
    """
    res = []
    for t in transforms:
        if t.is_rot():
            if n == 0 or geomtypes.eq(t.angle(), 2 * math.pi / n):
                axis = t.axis()
                if axis not in res and -axis not in res:
                    res.append(axis)
    return res


class ImproperSubgroupError(ValueError):
    "Raised when subgroup is not really a subgroup"


class Set(set, base.Orbitit):
    """
    Base class for the symmetry groups, which are sets of isometries.
    """
    init_pars = []
    debug = False
    # if True the isometry set consists of direct and indirect isometries else
    # it consists of direct isometries only if it is a group:
    mixed = False
    std_setup = None
    to_class = {}

    def __init__(self, *args):
        try:
            self.generator
        except AttributeError:
            self.generator = {}
        super().__init__(*args)
        self.short_string = True

    def __repr__(self):
        s = indent.Str(f"{base.find_module_class_name(self.__class__, __name__)}(\n")
        s = s.add_incr_line("[")
        s.incr()
        s = s.glue_line(',\n'.join(repr(e).reindent(s.indent) for e in self))
        s = s.add_decr_line("]")
        s.decr()
        s += ")"
        if __name__ != '__main__':
            s = s.insert(__name__)
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        result = {
            "class": base.class_to_json[self.__class__],
            "data": {},
        }
        if self.generator:
            result["data"]["generator"] = self.generator
        else:
            result["data"]["isometries"] = [e.repr_dict for e in self]
        return result

    @classmethod
    def from_json_dict(cls, repr_dict):
        """Recreate object from complete dict representation."""
        try:
            sub_class = cls.to_class[repr_dict["class"]]
        except KeyError as e:
            raise Exception(f'{repr_dict["class"]} not in {cls.to_class} (expected)') from e
        return sub_class.from_dict_data(repr_dict["data"])

    @classmethod
    def from_dict_data(cls, data):
        """Create object from dictionary data."""
        if "generator" in data:
            return cls(setup=data["generator"])  # pylint: disable=unexpected-keyword-arg
        if "isometries" in data:
            isoms = [base.json_to_class[i["class"]].from_json_dict(i) for i in data["isometries"]]
            if cls == Set:
                return cls(isoms)
            return cls(isometries=isoms)  # pylint: disable=unexpected-keyword-arg
        raise IndexError(f'missing "generator" or "isometries" in {data}')

    def __str__(self):
        def to_s():
            """Convert to string"""
            s = f'{self.__class__.__name__}([\n'
            for e in self:
                s = f'{s} {e},\n'
            s = f'{s}])'
            if __name__ != '__main__':
                s = f'{__name__}.{s}'
            return s
        if self.generator != {}:
            if self.short_string:
                s = f'{self.__class__.__name__}(setup={self.generator})'
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
                if not eq:
                    break
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
        # Set * geomtypes.Transform3
        return Set([e * o for e in self])

    def __rmul__(self, o):
        # Note rotation Set * Set is caught by __mul__
        # rotation Rot * Set
        return Set([o * e for e in self])

    def is_group(self):
        """Check whether self is a algebraic group"""
        # A group should at least have 'E', it cannot be empty
        if not self:
            return False
        this_is_group = True
        for e in self:
            # optimised away, done as part of next loop:
            # if not (e.inverse() in self):
            this_has_inverse = False
            for o in self:
                this_has_inverse = this_has_inverse | (e.inverse() == o)
                is_closed_for_this = e*o in self and o*e in self
                if not is_closed_for_this:
                    break
            if not this_has_inverse or not is_closed_for_this:
                this_is_group = False
                break

        return this_is_group
        # the following is not needed to check, is done implicitly:
        # and (geomtypes.E in self)

    def is_subgroup(self, o, check_group=True):
        """returns whether this is a subgroup of o)"""
        if len(self) > len(o):
            return False  # optimisation
        return (not check_group or self.is_group()) and self.issubset(o)

    def subgroup(self, o):
        """Make subgroup of self out of set of isometries or one isometry"""
        try:
            if isinstance(o, geomtypes.Transform3):
                # generate the quotient set THIS / o
                assert o in self
                subgroup = Set([o])
                subgroup.group()
                return subgroup

            # o is already a set
            for e in o:
                assert e in self, f'{e} not in {self.__class__.__name__}'
            subgroup = copy(o)
            # for optimisation: don't call group (slow) for self == o:
            if len(subgroup) < len(self):
                subgroup.group()
            elif len(subgroup) > len(self):
                raise ImproperSubgroupError(
                    f'{o.__class__.__name__} not subgroup of {self.__class__.__name__}'
                    ' (with this orientation)'
                )
            return subgroup

        # except ImproperSubgroupError:
        except AssertionError as e:
            raise ImproperSubgroupError(
                f'{o.__class__.__name__} not subgroup of {self.__class__.__name__}'
                ' (with this orientation)'
            ) from e

    def __truediv__(self, o):
        # this * subgroup: right quotient set
        # make sure o is a subgroup:
        if len(o) > len(self):
            return o.__truediv__(self)
        o = self.subgroup(o)
        assert len(o) <= len(self)
        # use a list of sets, since sets are unhashable
        quotient_set = []
        # use a big set for all elems found so for
        found_so_far = Set([])
        for te in self:
            q = te * o
            if q.get_one() not in found_so_far:
                quotient_set.append(q)
                found_so_far = found_so_far.union(q)
        return quotient_set

    quotient_set = __truediv__

    def __rdiv__(self, o):
        #  subgroup * self: left quotient set
        pass  # TODO

    def __contains__(self, o):
        # Needed for 'in' relationship: default doesn't work, it seems to
        # compare the elements id.
        for e in self:
            if e == o:
                return True
        return False

    def add(self, e):
        """Add element e to the set"""
        if e not in self:
            set.add(self, e)

    def update(self, o):
        """Update the set with new elements in o"""
        for e in o:
            self.add(e)

    def get_one(self):
        """Just get any element in the set.

        Try to return a direct isometry if possible.
        """
        e = None
        for e in self:
            if e.is_direct():
                return e
        return e

    def group(self, max_iter=50):
        """
        Tries to make a group out of the set of isometries

        If it succeeds within maxiter step this set is closed, contains the
        unit element and the set contains for every elements its inverse
        """
        result = copy(self)
        for e in self:
            result.add(e.inverse())
        result.add(geomtypes.E)
        self.clear()
        self.update(result.close(max_iter))

    def close(self, max_iter=5):
        """
        Return a closed set, if it can be generated within max_iter steps.
        """
        result = copy(self)
        for _ in range(max_iter):
            l_prev = len(result)
            result.update(result * result)
            l_new = len(result)
            if l_new == l_prev:
                break
        assert l_new == l_prev, \
            f"Couldn't close group after {max_iter} iterations"
        return result

    def chk_setup(self, setup):
        """Check whether all keys in setup are legitimate"""
        if setup != {} and not self.init_pars:
            logging.warning(
                "class %s doesn't handle any setup pars %s",
                self.__class__,
                list(setup.keys()),
            )
        for k in list(setup.keys()):
            found = False
            for p in self.init_pars:
                found |= p['par'] == k
                if found:
                    break
            if not found:
                assert  k == 'n' and self.n, (
                    f'Unknown parameter {k} in setup = {str(setup)} for {self.__class__.__name__}'
                )
        self.generator = setup

    @classmethod
    def remove_init_par(cls, label):
        """Remove an init_par with specified label.

        This is used for isometry sets like C2 with unspecified axis, which is created from C(n)
        where the 'n' would have been an init_par as well. With this method one can remove the
        parameter 'n', since that one isn't required anymore.
        """
        del_n = -1
        for i, par in enumerate(cls.init_pars):
            if par['par'] == label:
                del_n = i
        if del_n >= 0:
            del cls.init_pars[del_n]

    @property
    def setup(self):
        """Fetch the original setup"""
        return self.generator


def init_dict(**kwargs):
    """Create a dict with kwargs"""
    return kwargs


class E(Set):
    """Class representing the trivial symmetry that maps something on itself"""
    # TODO: make singular
    # Use method 2: https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    order = 1
    mixed = False

    def __init__(self, isometries=None, setup=None):
        if setup is None:
            setup = {}
        self.chk_setup(setup)
        if isometries:
            assert len(isometries) == 1, \
                f'Class E should contain exactly one isometry, got {len(isometries)}'
            assert isometries[0] == geomtypes.E, \
                f'Class E should only contain the isometry E, got {isometries[0]}'
        Set.__init__(self, [geomtypes.E])

    @property
    def repr_dict(self):
        return {
            "class": base.class_to_json[self.__class__],
            "data": {},
        }

    @classmethod
    def from_dict_data(cls, data):
        """Create object from dictionary data."""
        return cls()

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == E:
            return [E()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


E.subgroups = [E]


class ExI(Set):
    """Symmetry class containing E and the central inversion"""
    order = 2
    mixed = True
    direct_parent = E
    direct_parent_setup = {}

    def __init__(self, isometries=None, setup=None):
        if setup is None:
            setup = {}
        self.chk_setup(setup)
        if isometries:
            assert len(isometries) == 2, \
                'Class ExI should contain exactly two isometries'
            assert geomtypes.E in isometries and geomtypes.I in isometries, \
                'Class ExI should only contain the isometry E and I'
        Set.__init__(self, [geomtypes.E, geomtypes.I])

    @property
    def repr_dict(self):
        return {
            "class": base.class_to_json[self.__class__],
            "data": {},
        }

    @classmethod
    def from_dict_data(cls, data):
        """Create object from dictionary data."""
        return cls()

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == ExI:
            return [self]
        if sg == E:
            return [E()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


ExI.subgroups = [ExI, E]


def _cn_get_subgroups(n):
    """Add subgroup classes of Cn (with specific n, except own class)

    The own class (by calling C(n) cannot be added, since it leads to
    recursion.
    """
    return [C(i) for i in range(n//2, 0, -1) if n % i == 0]


class MetaCn(type(Set)):
    """Meta class for the algebraic group of class Cn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)


class Cn(Set, metaclass=MetaCn):
    """Class for the C2 symmetry group"""
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
        - n rotations around one n-fold axis
          (angle: i * 2pi/n, with 0 <= i < n)
        """
        if setup is None:
            setup = {}
        if isometries is not None:
            Set.__init__(self, isometries)
            min_angle = math.pi * 2
            axis = None
            for t in isometries:
                assert t.is_rot, f'Cn cannot contain any {t}'
                a = t.angle()
                if geomtypes.eq(a, 0):
                    continue
                min_angle = min(a, min_angle)
                if axis is None:
                    axis = t.axis()
                else:
                    ax = t.axis()
                    assert axis == ax or axis == -ax or geomtypes.eq(
                        t.angle(), 0),\
                        f'Cn can only have one unique axis ({axis} != {ax})'
                    axis = ax
            if axis is None:
                # Should be C1
                assert len(isometries) == 1, f'Expected C1, got {isometries}'
                axis = isometries[0].axis()
            n = int(round(2 * math.pi / min_angle))
            if self.n != 0:
                assert f"C{self.n} shouldn't be {n}-fold (alpha = {min_angle} rad)"
        else:
            self.chk_setup(setup)
            keys = list(setup.keys())
            if 'axis' in keys:
                axis = setup['axis']
            else:
                axis = copy(self.std_setup['axis'])
                self.generator['axis'] = axis
            if self.n != 0:
                n = self.n
            else:
                if 'n' in keys:
                    n = setup['n']
                else:
                    n = copy(self.std_setup['n'])
                    self.generator['n'] = n
                if n == 0:
                    n = 1
                # If self.n is hard-code (e.g. for C3)
                # then if you specify n it should be the correct value
                assert self.n in (0, n)
                self.n = n

            angle = 2 * math.pi / n
            try:
                r = geomtypes.Rot3(axis=axis, angle=angle)
            except TypeError:
                # assume axis has Rot3 type
                r = geomtypes.Rot3(axis=axis.axis(), angle=angle)

            isometries = [r]
            for _ in range(n-1):
                isometries.append(r * isometries[-1])
            Set.__init__(self, isometries)
        self.order = n
        self.rot_axes = {'n': axis}
        self.subgroups = _cn_get_subgroups(n)
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
            if sg.n == self.n:
                return [self]
            return[sg(setup={'axis': self.rot_axes['n']})]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


# dynamically create Cn classes:
def C(n):
    """Create class for Cn with specific n"""
    try:
        return __Cn_metas[n]
    except KeyError:
        if n == 1:
            __Cn_metas[n] = E
        else:
            class_name = f'C{n}'
            c_n = MetaCn(class_name,
                         (Cn,),
                         {'n': n,
                          'order': n,
                          'mixed': False,
                          'init_pars': _init_pars('Cn', n),
                          'std_setup': _std_setup('Cn', n)})
            c_n.subgroups = _cn_get_subgroups(n)
            c_n.subgroups.insert(0, c_n)
            c_n.remove_init_par('n')
            __Cn_metas[n] = c_n
            base.class_to_json[c_n] = class_name
            Set.to_class[class_name] = c_n
        return __Cn_metas[n]


def _c2ncn_get_subgroups(n):
    """Add subgroup classes of C2nCn (with specific n, except own class)

    The own class (by calling C(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n//2, 0, -1) if n % i == 0]
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


class MetaC2nCn(type(Set)):
    """Meta class for the algebraic group of class C2nCn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)


class C2nCn(Set, metaclass=MetaC2nCn):
    """Class for the C2nCn symmetry group"""
    mixed = True
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
        - n rotations around one n-fold axis
          (angle: i * 2pi/n, with 0 <= i < n)
        - n rotary inversions around one n-fold axis (angle: pi(1 + 2i)/n, with
          0 <= i < n)
        """
        if setup is None:
            setup = {}
        if isometries is not None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.chk_setup(setup)
            s = copy(setup)
            # TODO remove dependency on n, make this class C2nCn internal, use
            # only C2nC(n) and rename this to an __
            if 'n' not in s and self.n != 0:
                s['n'] = self.n
            # If self.n is hard-code (e.g. for C6C3)
            # then if you specify n it should be the correct value
            assert self.n in (0, s['n'])
            # TODO use direct parent here... (no dep on n)
            cn = Cn(setup=s)
            self.n = cn.n
            if self.n != 1:
                self.direct_parent_setup = copy(s)
            else:
                self.direct_parent_setup = None
            s['n'] = 2 * s['n']
            c2n = Cn(setup=s)
            Set.__init__(self, cn | ((c2n-cn) * geomtypes.I))
            self.rot_axes = {'n': cn.rot_axes['n']}
            self.order = c2n.order
            self.subgroups = _c2ncn_get_subgroups(self.n)
            self.subgroups.insert(0, C2nC(self.n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if isinstance(sg, MetaC2nCn):
            if sg.n == self.n:
                return [self]
            return [sg(setup={'axis': self.rot_axes['n']})]
        if isinstance(sg, MetaCn):
            return [sg(setup={'axis': self.rot_axes['n']})]
        if sg == E:
            return [E()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


# dynamically create C2nCn classes:
def C2nC(n):
    """Create class for CnxI with specific n"""
    try:
        return __C2nCn_metas[n]
    except KeyError:
        class_name = f'C{2*n}C{n}'
        c_2n_c_n = MetaC2nCn(class_name,
                             (C2nCn,),
                             {'n': n,
                              'order': 2 * n,
                              'mixed': True,
                              'direct_parent': C(n),
                              'init_pars': _init_pars('Cn', n),
                              'std_setup': _std_setup('Cn', n)})
        c_2n_c_n.subgroups = _c2ncn_get_subgroups(n)
        c_2n_c_n.subgroups.insert(0, c_2n_c_n)
        c_2n_c_n.remove_init_par('n')
        __C2nCn_metas[n] = c_2n_c_n
        base.class_to_json[c_2n_c_n] = class_name
        Set.to_class[class_name] = c_2n_c_n
        return __C2nCn_metas[n]


def _cnxi_get_subgroups(n):
    """Add subgroup classes of CnxI (with specific n, except own class)

    The own class (by calling C(n) cannot be added, since it leads to
    recursion.
    """
    # divisors of n
    divs = [i for i in range(n//2, 0, -1) if n % i == 0]
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
        m = n // 2
        # - if odd divisor: trivial, also have reflection
        # - if even divisor i: can only be added if (n / i) % 2 == 0
        g_c2ici = [C2nC(i) for i in range(1, m + 1)
                   if n % i == 0 and (i % 2 != 0 or (n / i) % 2 == 0)]
        g.extend(g_c2ici)
    # else: n odd: all divisors are odd as well: all C2iCi for divisors i will
    # have a reflection, while CnxI doesn't
    return _sort_and_del_dups(g)


class MetaCnxI(type(Set)):
    """Meta class for the algebraic group of class CnxI"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)


class CnxI(Set, metaclass=MetaCnxI):
    """Class for the CnxI symmetry group"""
    mixed = True
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
        - n rotations around one n-fold axis
          (angle: i * 2pi/n, with 0 <= i < n)
        - n rotary inversions around one n-fold axis (angle: i * 2pi/n, with
          0 <= i < n)
        """
        if setup is None:
            setup = {}
        if isometries is not None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.chk_setup(setup)
            s = copy(setup)
            if 'n' not in s and self.n != 0:
                s['n'] = self.n
            # If self.n is hard-code (e.g. for C3xI)
            # then if you specify n it should be the correct value
            assert self.n in (0, s['n'])
            cn = Cn(setup=s)
            self.direct_parent = C(self.n)
            self.direct_parent_setup = copy(s)
            self.n = cn.n
            Set.__init__(self, cn * ExI())
            self.rot_axes = {'n': cn.rot_axes['n']}
            self.order = 2 * cn.order
            self.subgroups = _cnxi_get_subgroups(self.n)
            self.subgroups.insert(0, CxI(self.n))

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if isinstance(sg, MetaCnxI):
            if sg.n == self.n:
                return [self]
            return [sg(setup={'axis': self.rot_axes['n']})]
        if isinstance(sg, (MetaC2nCn, MetaCn)):
            return [sg(setup={'axis': self.rot_axes['n']})]
        if sg == ExI:
            return [ExI()]
        if sg == E:
            return [E()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


# dynamically create CnxI classes:
def CxI(n):
    """Create class for CnxI with specific n"""
    try:
        return __CnxI_metas[n]
    except KeyError:
        if n == 1:
            __CnxI_metas[n] = ExI
        else:
            class_name = f'C{n}xI'
            c_nxi = MetaCnxI(class_name,
                             (CnxI,),
                             {'n': n,
                              'order': 2 * n,
                              'mixed': True,
                              'direct_parent': C(n),
                              'init_pars': _init_pars('Cn', n),
                              'std_setup': _std_setup('Cn', n)})
            c_nxi.subgroups = _cnxi_get_subgroups(n)
            c_nxi.subgroups.insert(0, c_nxi)
            c_nxi.remove_init_par('n')
            __CnxI_metas[n] = c_nxi
            base.class_to_json[c_nxi] = class_name
            Set.to_class[class_name] = c_nxi
        return __CnxI_metas[n]


def _dncn_get_subgroups(n):
    """Add subgroup classes of DnCn (with specific n, except own class)

    The own class (by calling DnC(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n//2, 0, -1) if n % i == 0]
    g = [DnC(i) for i in divs]
    divs.insert(0, n)
    g.extend([C(i) for i in divs])
    return _sort_and_del_dups(g)


class MetaDnCn(type(Set)):
    """Meta class for the algebraic group of class DnCn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)


class DnCn(Set, metaclass=MetaDnCn):
    """Class for the DnCn symmetry group"""
    mixed = True
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
        - n rotations around one n-fold axis
          (angle: i * 2pi/n, with 0 <= i < n)
        - n reflections in planes that share the n-fold axis.
        """
        if setup is None:
            setup = {}
        if isometries is not None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            s = {}
            self.chk_setup(setup)
            if 'n' not in setup:
                if self.n != 0:
                    s['n'] = self.n
                else:
                    s['n'] = copy(self.std_setup['n'])
            else:
                s['n'] = setup['n']
                # If self.n is hard-code (e.g. for D3C3)
                # then if you specify n it should be the correct value
                assert self.n in (0, s['n'])
            if 'axis_n' in setup:
                s['axis'] = setup['axis_n']
            else:
                s['axis'] = copy(self.std_setup['axis_n'])
            cn = Cn(setup=s)
            self.direct_parent = C(self.n)
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
            self.subgroups = _dncn_get_subgroups(self.n)
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
            return _get_alternative_subgroups(
                sg, self.refl_normals,
                lambda r, p: p in r.refl_normals,
                lambda sg, p: sg(setup={'axis_n': self.rot_axes['n'],
                                        'normal_r': p}))
        if isinstance(sg, MetaC2nCn):
            assert sg.n == 1, \
                f'Only C2C1 can be subgroup of DnCn (n={sg.n})'
            # C2C1 ~= E, plus reflection, with normal == rotation axis (0)
            # provide the normal of the one reflection:
            return [sg(setup={'axis': self.refl_normals[0]})]
        if isinstance(sg, MetaCn):
            return [sg(setup={'axis': self.rot_axes['n']})]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


# dynamically create DnCn classes:
def DnC(n):
    """Create class for DnCn with specific n"""
    try:
        return __DnCn_metas[n]
    except KeyError:
        if n == 1:
            __DnCn_metas[n] = C2C1
        else:
            class_name = f'D{n}C{n}'
            d_n_c_n = MetaDnCn(class_name,
                               (DnCn,),
                               {'n': n,
                                'order': 2 * n,
                                'mixed': True,
                                'direct_parent': C(n),
                                'init_pars': _init_pars('DnCn', n),
                                'std_setup': _std_setup('DnCn', n)})
            d_n_c_n.subgroups = _dncn_get_subgroups(n)
            d_n_c_n.subgroups.insert(0, d_n_c_n)
            d_n_c_n.remove_init_par('n')
            __DnCn_metas[n] = d_n_c_n
            base.class_to_json[d_n_c_n] = class_name
            Set.to_class[class_name] = d_n_c_n
        return __DnCn_metas[n]


def _dn_get_subgroups(n):
    """Add subgroup classes of Dn (with specific n, except own class)

    The own class (by calling D2nD(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n//2, 0, -1) if n % i == 0]
    g = [D(i) for i in divs]
    divs.insert(0, n)
    g.extend([C(i) for i in divs])
    return _sort_and_del_dups(g)


class MetaDn(type(Set)):
    """Meta class for the algebraic group of class Dn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)


class Dn(Set, metaclass=MetaDn):
    """Class for the Dn symmetry group"""
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
        - n rotations around one n-fold axis
          (angle: i * 2pi/n, with 0 <= i < n)
        - n halfturns around axes perpendicular to the n-fold axis
        """
        if setup is None:
            setup = {}
        if isometries is not None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.chk_setup(setup)
            keys = list(setup.keys())
            if 'axis_n' in keys:
                axis_n = setup['axis_n']
            else:
                axis_n = copy(self.std_setup['axis_n'])
                self.generator['axis_n'] = axis_n
            if 'axis_2' in keys:
                axis_2 = setup['axis_2']
            else:
                axis_2 = copy(self.std_setup['axis_2'])
                self.generator['axis_2'] = axis_2
            if self.n != 0:
                # If self.n is hard-code (e.g. for D3)
                # then if you specify n it should be the correct value
                assert 'n' not in setup or setup['n'] == self.n, \
                    f'Ooops: n not defined right for {self.__class__.__name__}'
                n = self.n
            else:
                if 'n' in keys:
                    n = setup['n']
                else:
                    n = 2
                self.generator['n'] = n
                if n == 0:
                    n = 1

            h = geomtypes.HalfTurn3(axis=axis_2)
            cn = Cn(setup={'axis': axis_n, 'n': n})
            isometries = list(cn)
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
            self.subgroups = _dn_get_subgroups(self.n)
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
            if sg.n == 2:  # sg = C2
                isoms = [
                    sg(setup={'axis': self.rot_axes[2][i]})
                    for i in range(len(self.rot_axes[2]))
                ]
                if self.n % 2 == 0:  # if D2, D4, etc
                    isoms.insert(0, sg(setup={'axis': self.rot_axes['n']}))
                return isoms
            return [sg(setup={'axis': self.rot_axes['n']})]
        if sg.n > self.n:
            return []

        if isinstance(sg, MetaDn):
            if sg.n == self.n:
                return [self]
            return _get_alternative_subgroups(
                sg, self.rot_axes[2],
                lambda r, p: p in r.rot_axes[2],
                lambda sg, p: sg(setup={'axis_n': self.rot_axes['n'],
                                        'axis_2': p}))
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


# dynamically create Dn classes:
def D(n):
    """Create class for Dn with specific n"""
    try:
        return __Dn_metas[n]
    except KeyError:
        if n == 1:
            __Dn_metas[n] = C2
        else:
            class_name = f'D{n}'
            d_n = MetaDn(class_name,
                         (Dn,),
                         {'n': n,
                          'order': 2 * n,
                          'mixed': False,
                          'init_pars': _init_pars('Dn', n),
                          'std_setup': _std_setup('Dn', n)})
            d_n.subgroups = _dn_get_subgroups(n)
            d_n.subgroups.insert(0, d_n)
            d_n.remove_init_par('n')
            __Dn_metas[n] = d_n
            base.class_to_json[d_n] = class_name
            Set.to_class[class_name] = d_n
        return __Dn_metas[n]


def _dnxi_get_subgroups(n):
    """Add subgroup classes of DnxI (with specific n, except own class)

    The own class (by calling DxI(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n//2, 0, -1) if n % i == 0]
    # DxI if n odd and divisor odd, or n even and divisor even
    g = [DxI(i) for i in divs if n % 2 == i % 2]
    divs.insert(0, n)
    # CxI if n odd and divisor odd, or n even and divisor even
    g.extend([CxI(i) for i in divs if n % 2 == i % 2])
    # only needed for n even, since
    # if n odd, there are no even divisors
    if n % 2 == 0:
        # as long as n / divisor is even (then the half-turns are covered)
        g.extend([D2nD(i) for i in divs if (n / i) % 2 == 0])
        g.extend([C2nC(i) for i in divs if (n / i) % 2 == 0])
    g.extend([D(i) for i in divs])
    g.extend([C(i) for i in divs])
    g.extend([DnC(i) for i in divs])
    return _sort_and_del_dups(g)


class MetaDnxI(type(Set)):
    """Meta class for the algebraic group of class DnxI"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)


class DnxI(Set, metaclass=MetaDnxI):
    """Class for the DnxI symmetry group"""
    mixed = True
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
        - n rotations around one n-fold axis
          (angle: i * 2pi/n, with 0 <= i < n)
        - n halfturns around axes perpendicular to the n-fold axis
        - n rotary inversions around one n-fold axis (angle: i * 2pi/n, with
          0 <= i < n). For n even one of these becomes a reflection in a plane
          perpendicular to the n-fold axis.
        - n reflections in planes that contain the n-fold axis. The normals of
          the reflection planes are perpendicular to the halfturn axes.
        """
        if setup is None:
            setup = {}
        if isometries is not None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.chk_setup(setup)
            s = copy(setup)
            if 'n' not in s and self.n != 0:
                s['n'] = self.n
            # If self.n is hard-code (e.g. for D3xI)
            # then if you specify n it should be the correct value
            assert self.n in (0, s['n'])
            dn = Dn(setup=s)
            self.direct_parent = D(self.n)
            self.direct_parent_setup = copy(s)
            Set.__init__(self, dn * ExI())
            self.rot_axes = {'n': dn.rot_axes['n'], 2: dn.rot_axes[2][:]}
            self.n = dn.n
            self.refl_normals = []
            for isom in self:
                if isom.is_refl():
                    self.refl_normals.append(isom.plane_normal())
            self.order = 2 * dn.order
            self.subgroups = _dnxi_get_subgroups(self.n)
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
            return _get_alternative_subgroups(
                sg, self.rot_axes[2],
                lambda r, p: p in r.rot_axes[2],
                lambda sg, p: sg(setup={'axis_n': self.rot_axes['n'],
                                        'axis_2': p}))
        if isinstance(sg, (MetaDn, MetaD2nDn)):
            return _get_alternative_subgroups(
                sg, self.rot_axes[2],
                lambda r, p: p in r.rot_axes[2],
                lambda sg, p: sg(setup={'axis_n': self.rot_axes['n'],
                                        'axis_2': p}))
        if isinstance(sg, MetaDnCn):
            return _get_alternative_subgroups(
                sg, self.rot_axes[2],
                lambda r, p: p in r.refl_normals,
                lambda sg, p: sg(setup={'axis_n': self.rot_axes['n'],
                                        'normal_r': p}))
        if isinstance(sg, MetaC2nCn):
            if sg.n == 1:
                return [sg(setup={'axis': r}) for r in self.refl_normals]
            return [sg(setup={'axis': self.rot_axes['n']})]
        if isinstance(sg, (MetaCn, MetaCnxI)):
            # standard realisation:
            real_std = sg(setup={'axis': self.rot_axes['n']})
            if sg.n == 2:
                # special realisation (note D1xI ~= C2xI or D1 ~= C2)
                real_spc = [sg(setup={'axis': r}) for r in self.rot_axes[2]]
                if self.n % 2 != 0:
                    return real_spc
                real_spc.insert(0, real_std)
                return real_spc
            return [real_std]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


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
            class_name = f'D{n}xI'
            dnxi = MetaDnxI(class_name,
                            (DnxI,),
                            {'n': n,
                             'order': 4 * n,
                             'mixed': True,
                             'direct_parent': D(n),
                             'init_pars': _init_pars('Dn', n),
                             'std_setup': _std_setup('Dn', n)})
            dnxi.subgroups = _dnxi_get_subgroups(n)
            dnxi.subgroups.insert(0, dnxi)
            dnxi.remove_init_par('n')
            __DnxI_metas[n] = dnxi
            base.class_to_json[dnxi] = class_name
            Set.to_class[class_name] = dnxi
        return __DnxI_metas[n]


def _d2ndn_get_subgroups(n):
    """Add subgroup classes of D2nDn (with specific n, except own class)

    The own class (by calling D2nD(n) cannot be added, since it leads to
    recursion.
    """
    # divisors (incl 1)
    divs = [i for i in range(n//2, 0, -1) if n % i == 0]
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


class MetaD2nDn(type(Set)):
    """Meta class for the algebraic group of class D2nDn"""
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)


class D2nDn(Set, metaclass=MetaD2nDn):
    """Class for the D2nDn symmetry group"""
    mixed = True
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
        - n rotations around one n-fold axis
          (angle: i * 2pi/n, with 0 <= i < n)
        - n halfturns around axes perpendicular to the n-fold axis
        - n rotary inversions around one n-fold axis (angle: pi(1 + 2i)/n, with
          0 <= i < n). For n odd one of these becomes a reflection in a plane
          perpendicular to the n-fold axis.
        - n reflections in planes that contain the n-fold axis. The normal of
          the reflection planes lie in the middle between two halfturns.
        """
        if setup is None:
            setup = {}
        if isometries is not None:
            # TODO: add some asserts
            Set.__init__(self, isometries)
        else:
            self.chk_setup(setup)
            s = copy(setup)
            if 'n' not in s and self.n != 0:
                s['n'] = self.n
            # If self.n is hard-code (e.g. for D6D3)
            # then if you specify n it should be the correct value
            assert self.n in (0, s['n'])
            dn = Dn(setup=s)
            self.n = dn.n
            self.direct_parent = D(self.n)
            self.direct_parent_setup = copy(s)
            s['n'] = 2 * s['n']
            d2n = Dn(setup=s)
            Set.__init__(self, dn | ((d2n-dn) * geomtypes.I))
            self.rot_axes = dn.rot_axes
            self.refl_normals = []
            for isom in self:
                if isom.is_refl():
                    self.refl_normals.append(isom.plane_normal())
            self.order = d2n.order
            self.subgroups = _d2ndn_get_subgroups(self.n)
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
            return _get_alternative_subgroups(
                sg, self.rot_axes[2],
                lambda r, p: p in r.rot_axes[2],
                lambda sg, p: sg(setup={'axis_n': self.rot_axes['n'],
                                        'axis_2': p}))
        if isinstance(sg, MetaDn):
            return _get_alternative_subgroups(
                sg, self.rot_axes[2],
                lambda r, p: p in r.rot_axes[2],
                lambda sg, p: sg(setup={'axis_n': self.rot_axes['n'],
                                        'axis_2': p}))
        if isinstance(sg, MetaDnCn):
            if sg.n == 2 and self.n % 2 != 0:
                return [sg(setup={'axis_n': h,
                                  'normal_r': self.rot_axes['n']})
                        for h in self.rot_axes[2]]
            return _get_alternative_subgroups(
                sg, self.refl_normals,
                lambda r, p: p in r.refl_normals,
                lambda sg, p: sg(setup={'axis_n': self.rot_axes['n'],
                                        'normal_r': p}))
        if isinstance(sg, MetaC2nCn):
            if sg.n == 1:
                sg_base = [sg(setup={'axis': r}) for r in self.refl_normals]
                if self.n % 2 != 0:
                    sg_base.insert(0, sg(setup={'axis': self.rot_axes['n']}))
                return sg_base
            return [sg(setup={'axis': self.rot_axes['n']})]
        if isinstance(sg, MetaCn):
            if sg.n == 2:
                sg_base = [sg(setup={'axis': h}) for h in self.rot_axes[2]]
                if self.n % 2 == 0:
                    sg_base.insert(0, sg(setup={'axis': self.rot_axes['n']}))
                return sg_base
            return [sg(setup={'axis': self.rot_axes['n']})]
        # Note: no DnxI, CnxI subgroups exist, see _d2ndn_get_subgroups
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


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
            class_name = f'D{2*n}D{n}'
            d_2n_d_n = MetaD2nDn(class_name,
                                 (D2nDn,),
                                 {'n': n,
                                  'order': 4 * n,
                                  'mixed': True,
                                  'direct_parent': D(n),
                                  'init_pars': _init_pars('Dn', n),
                                  'std_setup': _std_setup('Dn', n)})
            d_2n_d_n.subgroups = _d2ndn_get_subgroups(n)
            d_2n_d_n.subgroups.insert(0, d_2n_d_n)
            d_2n_d_n.remove_init_par('n')
            __D2nDn_metas[n] = d_2n_d_n
            base.class_to_json[d_2n_d_n] = class_name
            Set.to_class[class_name] = d_2n_d_n
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
        if isometries is not None:
            assert len(isometries) == self.order, f"{self.order} != {len(isometries)}"
            Set.__init__(self, isometries)
            self.rot_axes = {
                2: get_axes(isometries, 2),
                3: get_axes(isometries, 3)}
        else:
            self.chk_setup(setup)
            axes = list(setup.keys())
            if 'o2axis0' in axes:
                o2axis0 = setup['o2axis0']
            else:
                o2axis0 = copy(self.std_setup['o2axis0'])
            if 'o2axis1' in axes:
                o2axis1 = setup['o2axis1']
            else:
                o2axis1 = copy(self.std_setup['o2axis1'])
            self.generator = {
                'o2axis0': o2axis0,
                'o2axis1': o2axis1,
            }
            d2 = _gen_d2(o2axis0, o2axis1)
            h0, h1, h2 = d2
            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = _gen_a4_o3(d2)

            Set.__init__(self,
                         [geomtypes.E,
                          h0, h1, h2,
                          r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2])

            self.rot_axes = {
                2: [h0.axis(), h1.axis(), h2.axis()],
                3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()]}

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == A4:
            return [self]
        if sg == D2:
            o2a = self.rot_axes[2]
            return [D2(setup={'axis_n': o2a[0], 'axis_2': o2a[1]})]
        if sg == C2:
            o2a = self.rot_axes[2]
            return [C2(setup={'axis': a}) for a in o2a]
        if sg == C3:
            o3a = self.rot_axes[3]
            return [C3(setup={'axis': a}) for a in o3a]
        if sg == E:
            return [E()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


class S4A4(Set):
    """Class for the S4A4 symmetry group

    It is the complete symmetry group of a Tetrahedron.
    """
    init_pars = _init_pars('A4')
    std_setup = _std_setup('A4')
    order = 24
    mixed = True
    direct_parent = A4

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
        if isometries is not None:
            assert len(isometries) == self.order, f"{self.order} != {len(isometries)}"
            Set.__init__(self, isometries)
            self.rot_axes = {
                2: get_axes(isometries, 2),
                3: get_axes(isometries, 3)}
        else:
            self.chk_setup(setup)
            axes = list(setup.keys())
            if 'o2axis0' in axes:
                o2axis0 = setup['o2axis0']
            else:
                o2axis0 = copy(self.std_setup['o2axis0'])
            if 'o2axis1' in axes:
                o2axis1 = setup['o2axis1']
            else:
                o2axis1 = copy(self.std_setup['o2axis1'])
            self.direct_parent_setup = copy(setup)
            self.generator = {
                'o2axis0': o2axis0,
                'o2axis1': o2axis1,
            }
            d2 = _gen_d2(o2axis0, o2axis1)
            h0, h1, h2 = d2
            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = _gen_a4_o3(d2)

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
            Set.__init__(self, [geomtypes.E,
                                h0, h1, h2,
                                r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2,
                                s0, s1, s2, s3, s4, s5,
                                ri0_1, ri0_3, ri1_1, ri1_3, ri2_1, ri2_3])

            self.refl_normals = [pn0, pn1, pn2, pn3, pn4, pn5]
            self.rot_axes = {
                2: [h0.axis(), h1.axis(), h2.axis()],
                3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()]}

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        # S4A4, A4, D2nDn, DnCn, C2nCn, Dn, Cn
        # C3, C2, E
        if sg == S4A4:
            return [self]
        if sg == A4:
            o2a = self.rot_axes[2]
            return [sg(setup={'o2axis0': o2a[0], 'o2axis1': o2a[1]})]
        if sg == D4D2:
            o2a = self.rot_axes[2]
            l_o2a = len(o2a)
            return [sg(setup={'axis_n': o2a[i], 'axis_2': o2a[(i+1) % l_o2a]})
                    for i in range(l_o2a)]
        if sg == D3C3:
            isoms = []
            for o3 in self.rot_axes[3]:
                for rn in self.refl_normals:
                    if geomtypes.eq(rn*o3, 0):
                        isoms.append(sg(setup={'axis_n': o3, 'normal_r': rn}))
                        break
            assert len(isoms) == 4, f'len(isoms) == {len(isoms)} != 4'
            return isoms
        if sg == C4C2:
            return [C4C2(setup={'axis': a}) for a in self.rot_axes[2]]
        if sg == C3:
            return [sg(setup={'axis': a}) for a in self.rot_axes[3]]
        if sg == C2:
            return [sg(setup={'axis': a}) for a in self.rot_axes[2]]
        if sg == C2C1:
            return [sg(setup={'axis': normal}) for normal in self.refl_normals]
        if sg == E:
            return [E()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


class A4xI(Set):
    """Class for the A4xI symmetry group

    It contains the direct symmetries of a Tetrahedron combined with the
    central inversion.
    """
    init_pars = _init_pars('A4')
    std_setup = _std_setup('A4')
    order = 24
    mixed = True
    direct_parent = A4

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
        if isometries is not None:
            assert len(isometries) == self.order, f"{self.order} != {len(isometries)}"
            Set.__init__(self, isometries)
            self.rot_axes = {
                2: get_axes(isometries, 2),
                3: get_axes(isometries, 3)}
        else:
            self.chk_setup(setup)
            a4 = A4(setup=setup)
            self.generator = a4.generator
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
        if sg == A4:
            # other ways of orienting A4 into A4xI don't give anything new
            return [A4(setup={'o2axis0': self.rot_axes[2][0],
                              'o2axis1': self.rot_axes[2][1]})]
        if sg == D2xI:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis_n': o2a[0], 'axis_2': o2a[1]})]
        if sg == C3xI:
            o3a = self.rot_axes[3]
            return [sg(setup={'axis': a}) for a in o3a]
        if sg == D2:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis_n': o2a[0], 'axis_2': o2a[1]})]
        if sg == D2C2:
            isoms = []
            for o2 in self.rot_axes[2]:
                for rn in self.rot_axes[2]:
                    if geomtypes.eq(rn*o2, 0):
                        isoms.append(sg(setup={'axis_n': o2, 'normal_r': rn}))
                        break
            assert len(isoms) == 3, f'len(isoms) == {len(isoms)} != 3'
            return isoms
        if sg == C2xI:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis': a}) for a in o2a]
        if sg == C3:
            o3a = self.rot_axes[3]
            return [sg(setup={'axis': a}) for a in o3a]
        if sg == C2:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis': a}) for a in o2a]
        if sg == C2C1:
            o2a = self.rot_axes[2]
            return [sg(setup={'axis': a}) for a in o2a]
        if sg == ExI:
            return [sg()]
        if sg == E:
            return [sg()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


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
        if isometries is not None:
            assert len(isometries) == self.order, f"{self.order} != {len(isometries)}"
            Set.__init__(self, isometries)
            self.rot_axes = {
                2: get_axes(isometries, 2),
                3: get_axes(isometries, 3),
                4: get_axes(isometries, 4)}
        else:
            self.chk_setup(setup)
            axes = list(setup.keys())
            if 'o4axis0' in axes:
                o4axis0 = setup['o4axis0']
            else:
                o4axis0 = copy(self.std_setup['o4axis0'])
            if 'o4axis1' in axes:
                o4axis1 = setup['o4axis1']
            else:
                o4axis1 = copy(self.std_setup['o4axis1'])
            self.generator = {
                'o4axis0': o4axis0,
                'o4axis1': o4axis1,
            }
            d2 = _gen_d2(o4axis0, o4axis1)
            r1_1, r1_2, r2_1, r2_2, r3_1, r3_2, r4_1, r4_2 = _gen_a4_o3(d2)
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
                angle=HALFTURN)
            h1 = geomtypes.Rot3(
                axis=geomtypes.Rot3(axis=ax0, angle=3*EIGHTH_TURN) * ax1,
                angle=HALFTURN)
            h2 = geomtypes.Rot3(
                axis=geomtypes.Rot3(axis=ax1, angle=EIGHTH_TURN) * ax0,
                angle=HALFTURN)
            h3 = geomtypes.Rot3(
                axis=geomtypes.Rot3(axis=ax1, angle=3*EIGHTH_TURN) * ax0,
                angle=HALFTURN)
            h4 = geomtypes.Rot3(
                axis=geomtypes.Rot3(axis=ax2, angle=EIGHTH_TURN) * ax0,
                angle=HALFTURN)
            h5 = geomtypes.Rot3(
                axis=geomtypes.Rot3(axis=ax2, angle=3*EIGHTH_TURN) * ax0,
                angle=HALFTURN)
            Set.__init__(self, [geomtypes.E,
                                q0_1, q0_2, q0_3,
                                q1_1, q1_2, q1_3,
                                q2_1, q2_2, q2_3,
                                r1_1, r1_2, r2_1, r2_2,
                                r3_1, r3_2, r4_1, r4_2,
                                h0, h1, h2, h3, h4, h5])
            self.rot_axes = {
                2: [h0.axis(), h1.axis(), h2.axis(),
                    h3.axis(), h4.axis(), h5.axis()],
                3: [r1_1.axis(), r2_1.axis(), r3_1.axis(), r4_1.axis()],
                4: [ax0, ax1, ax2]}

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == S4:
            return [self]
        if sg == A4:
            # other ways of orienting A4 into S4 don't give anything new
            return [A4(setup={'o2axis0': self.rot_axes[4][0],
                              'o2axis1': self.rot_axes[4][1]})]
        if sg == D4:
            o4a = self.rot_axes[4]
            l_o4a = len(o4a)
            return [sg(setup={'axis_n': o4a[i], 'axis_2': o4a[(i+1) % l_o4a]})
                    for i in range(l_o4a)]
        if sg == D3:
            isoms = []
            for o3 in self.rot_axes[3]:
                for o2 in self.rot_axes[2]:
                    if geomtypes.eq(o2*o3, 0):
                        isoms.append(sg(setup={'axis_n': o3, 'axis_2': o2}))
                        break
            assert len(isoms) == 4, f'len(isoms) == {len(isoms)} != 4'
            return isoms
        if sg == D2:
            isoms = []
            # There are 2 kinds of D2:
            # 1. one consisting of the three 4-fold axes
            # 2. 3 consisting of a 4 fold axis and two 2-fold axes.
            o4a = self.rot_axes[4]
            isoms = [sg(setup={'axis_n': o4a[0], 'axis_2': o4a[1]})]
            for o4 in self.rot_axes[4]:
                for o2 in self.rot_axes[2]:
                    if geomtypes.eq(o2*o4, 0):
                        isoms.append(sg(setup={'axis_n': o4, 'axis_2': o2}))
                        break
            assert len(isoms) == 4, f'len(isoms) == {len(isoms)} != 4'
            return isoms
        if sg == C4:
            o4a = self.rot_axes[4]
            return [sg(setup={'axis': a}) for a in o4a]
        if sg == C3:
            o3a = self.rot_axes[3]
            return [sg(setup={'axis': a}) for a in o3a]
        if sg == C2:
            o4a = self.rot_axes[4]
            isoms = [sg(setup={'axis': a}) for a in o4a]
            o2a = self.rot_axes[2]
            isoms.extend([sg(setup={'axis': a}) for a in o2a])
            return isoms
        if sg == E:
            return [E()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


class S4xI(Set):
    """Class for the S4xI symmetry group

    This is the complete symmetry group of the cube or octahedron.
    """
    init_pars = _init_pars('S4')
    std_setup = _std_setup('S4')
    order = 48
    mixed = True
    direct_parent = S4

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
        if isometries is not None:
            assert len(isometries) == self.order, f"{self.order} != {len(isometries)}"
            Set.__init__(self, isometries)
            self.rot_axes = {
                2: get_axes(isometries, 2),
                3: get_axes(isometries, 3),
                4: get_axes(isometries, 4)}
        else:
            self.chk_setup(setup)
            s4 = S4(setup=setup)
            self.generator = s4.generator
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
        if sg == S4:
            # other ways of orienting S4 into S4xI don't give anything new
            return [sg(setup={'o4axis0': self.rot_axes[4][0],
                              'o4axis1': self.rot_axes[4][1]})]
        if sg in (A4xI, A4, S4A4):
            return [sg(setup={'o2axis0': self.rot_axes[4][0],
                              'o2axis1': self.rot_axes[4][1]})]
        if sg in (D4xI, D8D4, D4):
            o4a = self.rot_axes[4]
            l_o4a = len(o4a)
            return [sg(setup={'axis_n': o4a[i],
                              'axis_2': o4a[(i + 1) % l_o4a]})
                    for i in range(l_o4a)]
        if sg in (D3xI, D3):
            isoms = []
            for o3 in self.rot_axes[3]:
                for o2 in self.rot_axes[2]:
                    if geomtypes.eq(o2*o3, 0):
                        isoms.append(sg(setup={'axis_n': o3, 'axis_2': o2}))
                        break
            assert len(isoms) == 4, f'len(isoms) == {len(isoms)} != 4'
            return isoms
        if sg == D4C4:
            isoms = []
            for a4 in self.rot_axes[4]:
                for rn in self.rot_axes[2]:
                    if geomtypes.eq(rn*a4, 0):
                        isoms.append(sg(setup={'axis_n': a4, 'normal_r': rn}))
                        break
            return isoms
        if sg == D4D2:
            o4a = self.rot_axes[4]
            l_o4a = len(o4a)
            isoms = [sg(setup={'axis_n': o4a[i],
                               'axis_2': o4a[(i + 1) % l_o4a]})
                     for i in range(l_o4a)]
            o2a = self.rot_axes[2]
            for a4 in o4a:
                for a2 in o2a:
                    if geomtypes.eq(a2*a4, 0):
                        isoms.append(sg(setup={'axis_n': a4, 'axis_2': a2}))
                        break
            return isoms
        if sg in (D2xI, D2):
            o4a = self.rot_axes[4]
            isoms = [sg(setup={'axis_n': o4a[0], 'axis_2': o4a[1]})]
            o2a = self.rot_axes[2]
            for a4 in o4a:
                for a2 in o2a:
                    if geomtypes.eq(a2*a4, 0):
                        isoms.append(sg(setup={'axis_n': a4, 'axis_2': a2}))
                        break
            assert len(isoms) == 4, f'len(isoms) == {len(isoms)} != 4'
            return isoms
        if sg == D3C3:
            isoms = []
            for o3 in self.rot_axes[3]:
                for rn in self.rot_axes[2]:
                    if geomtypes.eq(rn*o3, 0):
                        isoms.append(sg(setup={'axis_n': o3, 'normal_r': rn}))
                        break
            assert len(isoms) == 4, f'len(isoms) == {len(isoms)} != 4'
            return isoms
        if sg in (C3xI, C3):
            o3a = self.rot_axes[3]
            return [sg(setup={'axis': a}) for a in o3a]
        if sg == D2C2:
            o4a = self.rot_axes[4]
            l_o4a = len(o4a)
            isoms = [sg(setup={'axis_n': o4a[i],
                               'normal_r': o4a[(i + 1) % l_o4a]})
                     for i in range(l_o4a)]
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
            assert len(isoms) == 12, f'len(isoms) == {len(isoms)} != 12'
            return isoms
        if sg in (C4xI, C4, C4C2):
            o4a = self.rot_axes[4]
            return [sg(setup={'axis': a}) for a in o4a]
        if sg in (C2xI, D1xI, C2, D1):
            o2a = self.rot_axes[4]
            o2a.extend(self.rot_axes[2])
            return [sg(setup={'axis': a}) for a in o2a]
        if sg == C2C1:
            isoms = [sg(setup={'axis': a}) for a in self.rot_axes[2]]
            isoms.extend([sg(setup={'axis': a}) for a in self.rot_axes[4]])
            return isoms
        if sg in (E, ExI):
            return [sg()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


def _gen_d2(o2axis0, o2axis1):
    """Return orthogonal halfturns for D2"""
    # if axes is specified as a transform:
    if isinstance(o2axis0, geomtypes.Transform3):
        o2axis0 = o2axis0.axis()
    if isinstance(o2axis1, geomtypes.Transform3):
        o2axis1 = o2axis1.axis()

    assert geomtypes.eq(geomtypes.Vec3(o2axis0) * geomtypes.Vec3(o2axis1),
                        0), "Error: axes not orthogonal"
    h0 = geomtypes.HalfTurn3(axis=o2axis0)
    h1 = geomtypes.Rot3(axis=o2axis1, angle=HALFTURN)
    return (h0, h1, h1 * h0)


def _gen_a4_o3(d2_half_turns):
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
    o3axis = geomtypes.Rot3(axis=cube_h0.axis(),
                            angle=ASIN_1_V3) * cube_h1.axis()
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
        self._sub_d2_setup = None
        self._sub_d3_setup = None
        self._sub_d5_setup = None
        self._sub_a4_setup = None
        if isometries is None and setup is None:
            setup = {}
        if isometries is not None:
            assert len(isometries) == self.order, f"{self.order} != {len(isometries)}"
            # TODO: more asserts?
            Set.__init__(self, isometries)
            self.rot_axes = {
                2: get_axes(isometries, 2),
                3: get_axes(isometries, 3),
                5: get_axes(isometries, 5)}
        else:
            self.chk_setup(setup)
            axes = list(setup.keys())
            if 'o3axis' in axes:
                o3axis = setup['o3axis']
            else:
                o3axis = copy(self.std_setup['o3axis'])
            if 'o5axis' in axes:
                o5axis = setup['o5axis']
            else:
                o5axis = copy(self.std_setup['o5axis'])
            self.generator = {
                'o3axis': o3axis,
                'o5axis': o5axis,
            }

            turn5 = 2 * math.pi / 5
            turn3 = 2 * math.pi / 3
            r0_1_5 = geomtypes.Rot3(axis=o5axis, angle=turn5)
            r0_1_3 = geomtypes.Rot3(axis=o3axis, angle=turn3)
            o3axis = ensure_axis_type(o3axis)
            o5axis = ensure_axis_type(o5axis)
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
            self.rot_axes = {2: o2axes, 3: o3axes, 5: o5axes}
            self._sub_a4_setup, self._sub_d5_setup, self._sub_d3_setup = \
                a5_get_std_subgroup_setups(self.rot_axes)

    @property
    def sub_a4_setup(self):
        """Set up orientations for subgroup A4"""
        if self._sub_a4_setup is None:
            self._sub_a4_setup = a5_sub_a4_setup(self.rot_axes)
        return self._sub_a4_setup

    @property
    def sub_d5_setup(self):
        """Set up orientations for subgroup D5"""
        if self._sub_d5_setup is None:
            self._sub_d5_setup = a5_sub_d5_setup(self.rot_axes)
        return self._sub_d5_setup

    @property
    def sub_d3_setup(self):
        """Set up orientations for subgroup D3"""
        if self._sub_d3_setup is None:
            self._sub_d3_setup = a5_sub_d3_setup(self.rot_axes)
        return self._sub_d3_setup

    @property
    def sub_d2_setup(self):
        """Set up orientations for subgroup D2"""
        # Similar to A4 (D2 is subgroup of A4)
        if self._sub_d2_setup is None:
            self._sub_d2_setup = [
                {'axis_n': s['o2axis0'], 'axis_2': s['o2axis1']}
                for s in self.sub_a4_setup]
        return self._sub_d2_setup

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == A5:
            return [self]
        if sg == A4:
            return [sg(setup=setup) for setup in self.sub_a4_setup]
        if sg == D5:
            return [sg(setup=setup) for setup in self.sub_d5_setup]
        if sg == D3:
            return [sg(setup=setup) for setup in self.sub_d3_setup]
        if sg == D2:
            return [sg(setup=setup) for setup in self.sub_d2_setup]
        if sg == C5:
            return [sg(setup={'axis': a}) for a in self.rot_axes[5]]
        if sg == C3:
            return [sg(setup={'axis': a}) for a in self.rot_axes[3]]
        if sg == C2:
            return [sg(setup={'axis': a}) for a in self.rot_axes[2]]
        if sg == E:
            return [sg()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


class A5xI(Set):  # pylint: disable=too-many-instance-attributes
    """Class for the A5xI symmetry group

    This is the complete symmetry group of the icosaheron or dodecahedron
    """
    init_pars = _init_pars('A5')
    std_setup = _std_setup('A5')
    order = 120
    mixed = True
    direct_parent = A5

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
        - 24 rotary inversions based on the 6 5-fold axes (1/5, 2/5, 3/5, 4/5)
        - 20 rotary inversions based on the 10 3-fold axes (1/3, 2/3)
        - 15 reflections
        """
        self._sub_d2_setup = None
        self._sub_d3_setup = None
        self._sub_d5_setup = None
        self._sub_a4_setup = None
        self._sub_d2c2_setup = None
        self._sub_d3c3_setup = None
        self._sub_d5c5_setup = None
        if isometries is None and setup is None:
            setup = {}
        if isometries is not None:
            assert len(isometries) == self.order, f"{self.order} != {len(isometries)}"
            # TODO: more asserts?
            Set.__init__(self, isometries)
            self.rot_axes = {
                2: get_axes(isometries, 2),
                3: get_axes(isometries, 3),
                5: get_axes(isometries, 5)}
        else:
            self.chk_setup(setup)
            a5 = A5(setup=setup)
            self.generator = a5.generator
            self.direct_parent_setup = copy(setup)
            Set.__init__(self, a5 * ExI())
            self.rot_axes = a5.rot_axes
            self._sub_a4_setup, self._sub_d5_setup, self._sub_d3_setup = \
                a5_get_std_subgroup_setups(self.rot_axes)

    @property
    def sub_a4_setup(self):
        """Set up orientations for subgroup A4"""
        if self._sub_a4_setup is None:
            self._sub_a4_setup = a5_sub_a4_setup(self.rot_axes)
        return self._sub_a4_setup

    @property
    def sub_d5_setup(self):
        """Set up orientations for subgroup D5"""
        if self._sub_d5_setup is None:
            self._sub_d5_setup = a5_sub_d5_setup(self.rot_axes)
        return self._sub_d5_setup

    @property
    def sub_d3_setup(self):
        """Set up orientations for subgroup D3"""
        if self._sub_d3_setup is None:
            self._sub_d3_setup = a5_sub_d3_setup(self.rot_axes)
        return self._sub_d3_setup

    @property
    def sub_d2_setup(self):
        """Set up orientations for subgroup D2"""
        # Similar to A4 (D2 is subgroup of A4)
        if self._sub_d2_setup is None:
            self._sub_d2_setup = [
                {'axis_n': s['o2axis0'], 'axis_2': s['o2axis1']}
                for s in self.sub_a4_setup]
        return self._sub_d2_setup

    # This one isn't copied from A5:
    @property
    def sub_d5c5_setup(self):
        """Set up orientations for subgroup D5C5"""
        # Similar to D5 (but different setup names)
        if self._sub_d5c5_setup is None:
            self._sub_d5c5_setup = [
                {'axis_n': s['axis_n'], 'normal_r': s['axis_2']}
                for s in self.sub_d5_setup]
        return self._sub_d5c5_setup

    @property
    def sub_d3c3_setup(self):
        """Set up orientations for subgroup D3C3"""
        # Similar to D3 (but different setup names)
        if self._sub_d3c3_setup is None:
            self._sub_d3c3_setup = [
                {'axis_n': s['axis_n'], 'normal_r': s['axis_2']}
                for s in self.sub_d3_setup]
        return self._sub_d3c3_setup

    @property
    def sub_d2c2_setup(self):
        """Set up orientations for subgroup D2C2"""
        # Similar to D2 (but different setup names)
        if self._sub_d2c2_setup is None:
            self._sub_d2c2_setup = [
                {'axis_n': s['axis_n'], 'normal_r': s['axis_2']}
                for s in self.sub_d2_setup]
        return self._sub_d2c2_setup

    def realise_subgroups(self, sg):
        """
        realise an array of possible oriented subgroups for non-oriented sg
        """
        assert isinstance(sg, type)
        if sg == A5xI:
            return [self]
        if sg == A5:
            # other ways of orienting A5 into A5xI don't give anything new
            return [sg(setup={'o3axis': self.rot_axes[3][0],
                              'o5axis': self.rot_axes[5][0]})]
        if sg in (A4xI, A4):
            return [sg(setup=setup) for setup in self.sub_a4_setup]
        if sg in (D5xI, D5):
            return [sg(setup=setup) for setup in self.sub_d5_setup]
        if sg == D5C5:
            return [sg(setup=setup) for setup in self.sub_d5c5_setup]
        if sg in (D3xI, D3):
            return [sg(setup=setup) for setup in self.sub_d3_setup]
        if sg == D3C3:
            return [sg(setup=setup) for setup in self.sub_d3c3_setup]
        if sg in (D2xI, D2):
            return [sg(setup=setup) for setup in self.sub_d2_setup]
        if sg == D2C2:
            return [sg(setup=setup) for setup in self.sub_d2c2_setup]
        if sg in (C5xI, C5):
            return [sg(setup={'axis': a}) for a in self.rot_axes[5]]
        if sg in (C3xI, C3):
            return [sg(setup={'axis': a}) for a in self.rot_axes[3]]
        if sg in (C2xI, C2, C2C1, D1xI, D1):
            return [sg(setup={'axis': a}) for a in self.rot_axes[2]]
        if sg in (E, ExI):
            return [sg()]
        raise ImproperSubgroupError(
            f'{sg.__class__.__name__} not subgroup of {self.__class__.__name__}'
        )


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

# Classes that support conversion from and to JSON:
Set.to_class["isometry"] = Set
Set.to_class["E"] = E
Set.to_class["ExI"] = ExI
Set.to_class["Cn"] = Cn
Set.to_class["CnxI"] = CnxI
Set.to_class["C2nCn"] = C2nCn
Set.to_class["Dn"] = Dn
Set.to_class["DnxI"] = DnxI
Set.to_class["D2nDn"] = D2nDn
Set.to_class["A4"] = A4
Set.to_class["A5"] = A5
Set.to_class["S4"] = S4
Set.to_class["S4A4"] = S4A4
Set.to_class["A4xI"] = A4xI
Set.to_class["A5xI"] = A5xI
Set.to_class["S4xI"] = S4xI
base.class_to_json[Set] = "isometry"
base.class_to_json[E] = "E"
base.class_to_json[ExI] = "ExI"
base.class_to_json[Cn] = "Cn"
base.class_to_json[CnxI] = "CnxI"
base.class_to_json[C2nCn] = "C2nCn"
base.class_to_json[Dn] = "Dn"
base.class_to_json[DnxI] = "DnxI"
base.class_to_json[D2nDn] = "D2nDn"
base.class_to_json[A4] = "A4"
base.class_to_json[A5] = "A5"
base.class_to_json[S4] = "S4"
base.class_to_json[S4A4] = "S4A4"
base.class_to_json[A4xI] = "A4xI"
base.class_to_json[A5xI] = "A5xI"
base.class_to_json[S4xI] = "S4xI"
