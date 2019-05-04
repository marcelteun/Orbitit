#! /usr/bin/python
#
# Copyright (C) 2019 Marcel Tunnissen
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

from copy import copy
import math
import unittest

import geomtypes
import isometry

class TestVec(unittest.TestCase):
    """Unit test subgroups"""

    def test_cnxi(self):
        """Test some subgroups in CnxI"""
        # Test one even with even and odd divisors:
        h = isometry.CxI(12)
        subgroups = h.subgroups
        expect = [
            # trivial:
            isometry.CxI(12),
            isometry.E,
            # all divisors CnxI
            isometry.CxI(6),
            isometry.CxI(4),
            isometry.CxI(3),
            isometry.CxI(2),
            isometry.ExI,
            # all divisors Cn
            isometry.C(12),
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
            # C2nCn: all odd divisors:
            isometry.C2nC(3),
            # C2nCn: even divisors, only if divide is even
            isometry.C2nC(6),
            isometry.C2nC(2),
            isometry.C2nC(1),
        ]
        # You could test the length, but that is less helpful in case of
        # failures
        for g in subgroups:
            self.assertTrue(g in expect,
                            msg='Extra subgroup {} in {}'.format(g, h))
        for g in expect:
            self.assertTrue(g in subgroups,
                            msg='Missing subgroup {} in {}'.format(g, h))

        # Test one odd with divisors:
        h = isometry.CxI(9)
        subgroups = h.subgroups
        expect = [
            # trivial:
            isometry.CxI(9),
            isometry.E,
            # all divisors CnxI
            isometry.CxI(3),
            isometry.ExI,
            # all divisors Cn
            isometry.C(9),
            isometry.C(3),
        ]
        for g in subgroups:
            self.assertTrue(g in expect,
                            msg='Extra subgroup {} in {}'.format(g, h))
        for g in expect:
            self.assertTrue(g in subgroups,
                            msg='Missing subgroup {} in {}'.format(g, h))

    def test_c2ncn(self):
        """Test some subgroups of C2nCn"""
        # Test one even with even and odd divisors:
        # Even C2nCn don't have reflections
        h = isometry.C2nC(12)
        subgroups = h.subgroups
        expect = [
            # trivial:
            isometry.C2nC(12),
            isometry.E,
            # All Cn:
            isometry.C(12),
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
            # C2nCn:
            #  - don't add odd divisors: have refl
            #  - even divisor: add if (n/i) % 2 != 0
            isometry.C2nC(4),
            # CnxI: no subgroups, since:
            #  - even divisors have reflection
            #  - odd divisors: since n even, n / odd is even. I.e. not mapped
            #    on rotated one.
        ]
        # You could test the length, but that is less helpful in case of
        # failures
        for g in subgroups:
            self.assertTrue(g in expect,
                            msg='Extra subgroup {} in {}'.format(g, h))
        for g in expect:
            self.assertTrue(g in subgroups,
                            msg='Missing subgroup {} in {}'.format(g, h))
        # Test one odd
        # Odd C2nCn have reflections
        h = isometry.C2nC(15)
        subgroups = h.subgroups
        expect = [
            # trivial:
            isometry.C2nC(15),
            isometry.E,
            # All Cn:
            isometry.C(15),
            isometry.C(5),
            isometry.C(3),
            # C2nCn:
            #  - add all divisors, since all are odd (since n is odd)
            isometry.C2nC(15),
            isometry.C2nC(5),
            isometry.C2nC(3),
            # CnxI: no subgroups:
            #  - all divisors are odd (since n odd), i.e. no reflections
        ]
        # You could test the length, but that is less helpful in case of
        # failures
        for g in subgroups:
            self.assertTrue(g in expect,
                            msg='Extra subgroup {} in {}'.format(g, h))
        for g in expect:
            self.assertTrue(g in subgroups,
                            msg='Missing subgroup {} in {}'.format(g, h))

    def test_dncn(self):
        """Test some subgroups of C2nCn"""
        # Test one even with even and odd divisors:
        # Even C2nCn don't have reflections
        h = isometry.DnC(12)
        subgroups = h.subgroups
        expect = [
            # trivial:
            isometry.DnC(12),
            isometry.E,
            # all divisors:
            isometry.DnC(6),
            isometry.DnC(4),
            isometry.DnC(3),
            isometry.DnC(2),
            # isometry.DnC(2) ~= C2
            # E plus reflection:
            isometry.C2nC(1),
            # All Cn:
            isometry.C(12),
            isometry.C(6),
            isometry.C(4),
            isometry.C(3),
            isometry.C(2),
        ]
        # You could test the length, but that is less helpful in case of
        # failures
        for g in subgroups:
            self.assertTrue(g in expect,
                            msg='Extra subgroup {} in {}'.format(g, h))
        for g in expect:
            self.assertTrue(g in subgroups,
                            msg='Missing subgroup {} in {}'.format(g, h))
        # Test one odd
        # Odd C2nCn have reflections
        h = isometry.C2nC(15)
        subgroups = h.subgroups
        expect = [
            # trivial:
            isometry.C2nC(15),
            isometry.E,
            # All Cn:
            isometry.C(15),
            isometry.C(5),
            isometry.C(3),
            # C2nCn:
            #  - add all divisors, since all are odd (since n is odd)
            isometry.C2nC(15),
            isometry.C2nC(5),
            isometry.C2nC(3),
            # CnxI: no subgroups:
            #  - all divisors are odd (since n odd), i.e. no reflections
        ]
        # You could test the length, but that is less helpful in case of
        # failures
        for g in subgroups:
            self.assertTrue(g in expect,
                            msg='Extra subgroup {} in {}'.format(g, h))
        for g in expect:
            self.assertTrue(g in subgroups,
                            msg='Missing subgroup {} in {}'.format(g, h))

print 'testing creation of set',
g = isometry.Set([geomtypes.HX, geomtypes.HY])
print '....ok'
#print 'Initialised set g:', g
print "testing 'in' relation",
assert geomtypes.Rot3(axis = [1, 0, 0], angle = geomtypes.HALF_TURN) in g
assert geomtypes.Rot3(axis = [-1, 0, 0], angle = -geomtypes.HALF_TURN) in g
print '......ok'
print "testing 'close' function",
cg = g.close()
#print 'isometry.Set g after closing:'
#print cg
assert len(cg) == 4
assert geomtypes.HX in cg
assert geomtypes.HY in cg
assert geomtypes.HZ in cg
assert geomtypes.E in cg
print '...ok'

print 'testing creation of set',
g = isometry.Set([geomtypes.Rot3(axis = geomtypes.UX, angle = geomtypes.QUARTER_TURN)])
print '....ok'
print "testing 'in' relation",
geomtypes.Rot3(axis =  geomtypes.UX, angle = geomtypes.QUARTER_TURN)  in g
geomtypes.Rot3(axis = -geomtypes.UX, angle = -geomtypes.QUARTER_TURN) in g
print '......ok'
print "testing 'close' function",
cg = g.close()
#print 'isometry.Set g after closing:'
#print cg
assert len(cg) == 4
geomtypes.Rot3(axis =  geomtypes.Vec3([1, 0, 0]), angle = geomtypes.QUARTER_TURN)  in cg
geomtypes.Rot3(axis = -geomtypes.Vec3([1, 0, 0]), angle = -geomtypes.QUARTER_TURN) in cg
assert geomtypes.HX in cg
assert geomtypes.E in cg
print '...ok'

print 'testing creation of isometry.A4',
a4 = isometry.A4(setup = isometry.setup(o2axis0 = geomtypes.UX, o2axis1= geomtypes.UY))
print '.....ok'
print 'checking result',
assert len(a4) == 12
assert geomtypes.E in a4
assert geomtypes.HX in a4
assert geomtypes.HY in a4
assert geomtypes.HZ in a4
t0 = geomtypes.Rot3(axis = [1,  1,  1], angle =   geomtypes.THIRD_TURN)
assert t0 in a4
t1 = geomtypes.Rot3(axis = [1,  1,  1], angle = 2*geomtypes.THIRD_TURN)
assert t1 in a4
t2 = geomtypes.Rot3(axis = [1, -1,  1], angle =   geomtypes.THIRD_TURN)
assert t2 in a4
t3 = geomtypes.Rot3(axis = [1, -1,  1], angle = 2*geomtypes.THIRD_TURN)
assert t3 in a4
t4 = geomtypes.Rot3(axis = [1, -1, -1], angle =   geomtypes.THIRD_TURN)
assert t4 in a4
t5 = geomtypes.Rot3(axis = [1, -1, -1], angle = 2*geomtypes.THIRD_TURN)
assert t5 in a4
t6 = geomtypes.Rot3(axis = [1,  1, -1], angle =   geomtypes.THIRD_TURN)
assert t6 in a4
t7 = geomtypes.Rot3(axis = [1,  1, -1], angle = 2*geomtypes.THIRD_TURN)
assert t7 in a4
print '............ok'

print 'testing creation of isometry.A4',
a4 = isometry.A4(
        setup = isometry.setup(
            # try list argument
            o2axis0 = [1, 1, 1],
            # try Rot3 argument
            o2axis1 = geomtypes.HalfTurn3(axis=[1, -1, 0])
        )
    )
#print 'isometry.A4(o2axis0 = [1, 1, 1], o2axis1 = [1, -1, 0])'
print '.....ok'
# this a4 is the above a4 repositioned as follows:
r0 = geomtypes.Rot3(axis = geomtypes.UZ, angle = geomtypes.QUARTER_TURN / 2)
r1 = geomtypes.Rot3(axis = [1, -1, 0], angle = math.atan(1/math.sqrt(2)))
r = r1 * r0
print 'checking result',
assert len(a4) == 12
assert geomtypes.E in a4
assert geomtypes.HalfTurn3(axis=r*geomtypes.UX) in a4
assert geomtypes.HalfTurn3(axis=r*geomtypes.UY) in a4
assert geomtypes.HalfTurn3(axis=r*geomtypes.UZ) in a4
assert geomtypes.Rot3(axis = r * t0.axis(), angle =   geomtypes.THIRD_TURN) in a4
assert geomtypes.Rot3(axis = r * t1.axis(), angle = 2*geomtypes.THIRD_TURN) in a4
assert geomtypes.Rot3(axis = r * t2.axis(), angle =   geomtypes.THIRD_TURN) in a4
assert geomtypes.Rot3(axis = r * t3.axis(), angle = 2*geomtypes.THIRD_TURN) in a4
assert geomtypes.Rot3(axis = r * t4.axis(), angle =   geomtypes.THIRD_TURN) in a4
assert geomtypes.Rot3(axis = r * t5.axis(), angle = 2*geomtypes.THIRD_TURN) in a4
assert geomtypes.Rot3(axis = r * t6.axis(), angle =   geomtypes.THIRD_TURN) in a4
assert geomtypes.Rot3(axis = r * t7.axis(), angle = 2*geomtypes.THIRD_TURN) in a4
print '............ok'
#print a4
print 'test grouping this',
ca4 = copy(a4)
a4.group(2)
assert a4 == ca4
print '.........ok'

########################################################################
# Quotient isometry.Set:
a4 = isometry.A4(setup = isometry.setup(o2axis0 = geomtypes.UX, o2axis1= geomtypes.UY))
assert len(a4) == 12
# print 'group a4:'
# print a4
d2 = isometry.Set([geomtypes.HX, geomtypes.HY])
d2.group()
assert len(d2) == 4
# print 'has a subgroup D2:'
# print d2
print 'test quotient set: isometry.A4/D2',
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
# check if isometry.A4 / D2 is a partition of isometry.A4:
for i in range(len(q)-1):
    s = q[i]
    for transform in s:
        for j in range(i+1, len(q)):
            assert not transform in q[j]
print '...ok'

########################################################################
# Quotient isometry.Set:
print 'test isSubgroup: isometry.A4, isometry.S4',
s4 = isometry.S4()
a4 = isometry.A4()
assert a4.isSubgroup(s4)
assert not s4.isSubgroup(a4)
a4.add(geomtypes.I)
assert not a4.isSubgroup(s4)
print '....ok'

if __name__ == '__main__':
    unittest.main()
    print 'success!'
