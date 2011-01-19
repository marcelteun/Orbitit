#!/usr/bin/python
#
# Copyright (C) 2008 Marcel Tunnissen
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
# $Log$
#


import pygsl._numobj as numx
from pygsl  import multiroots, errno
import pygsl
import copy

import Heptagons
import GeomTypes

H         = numx.sin(  numx.pi / 7)
RhoH      = numx.sin(2*numx.pi / 7)
SigmaH    = numx.sin(3*numx.pi / 7)
Rho       = RhoH / H
Sigma     = SigmaH / H

# since GeomTypes.quat doesn't work well with multiroots...
def quatRot(axis, angle):
    assert not (GeomTypes.eq(axis[0], 0) and
	    GeomTypes.eq(axis[1], 0) and
	    GeomTypes.eq(axis[2], 0)
	), 'Axis cannot be (0, 0, 0) %s ' % str(axis)
    norm = numx.sqrt(axis[0]*axis[0] + axis[1]*axis[1] + axis[2]*axis[2])
    sa = numx.sin(angle/2)
    ca = numx.cos(angle/2)
    q0 = [sa*a/norm for a in axis]
    q1 = [-q for q in q0]
    q0.insert(0, ca)
    q1.insert(0, ca)
    return (q0, q1)

def quatMult(v, w):
    return [
	v[0]*w[0] - v[1]*w[1] - v[2] * w[2] - v[3] * w[3],
	v[0]*w[1] + v[1]*w[0] + v[2] * w[3] - v[3] * w[2],
	v[0]*w[2] - v[1]*w[3] + v[2] * w[0] + v[3] * w[1],
	v[0]*w[3] + v[1]*w[2] - v[2] * w[1] + v[3] * w[0]
    ]

def rotate(v, q):
    w = [0, v[0], v[1], v[2]]
    r = quatMult(q[0], w)
    r = quatMult(r, q[1])
    return GeomTypes.Vec(r[1:])

class TriangleAlt:
    strip1loose     = 0
    stripI          = 1
    stripII         = 2
    star            = 3
    star1loose      = 4
    alt_strip1loose = 5
    alt_stripI      = 6
    alt_stripII     = 7

Stringify = {
    TriangleAlt.strip1loose     : 'strip 1 loose',
    TriangleAlt.stripI          : 'strip I',
    TriangleAlt.stripII         : 'strip II',
    TriangleAlt.star            : 'star',
    TriangleAlt.star1loose      : 'star 1 loose',
    TriangleAlt.alt_strip1loose : 'alt strip 1 loose',
    TriangleAlt.alt_stripI      : 'alt strip I',
    TriangleAlt.alt_stripII     : 'alt strip II',
}

class Fold:
    parallel  = 0
    trapezium = 1
    w         = 2
    triangle  = 3
    star      = 4

    def __init__(this, f = 0):
	this.set(f)

    def set(this, f):
	assert (f >= this.parallel and f <= this.star)
	this.fold = f

    def __str__(this):
	if (this.fold == this.parallel):
	    return 'parallel'
	elif (this.fold == this.trapezium):
	    return 'trapezium'
	elif (this.fold == this.w):
	    return 'w'
	elif (this.fold == this.triangle):
	    return 'triangle'
	elif (this.fold == this.star):
	    return 'star'
	else:
	    return None

fold = Fold()

def FoldedRegularHeptagonsS4A4(x, params):
    """Calculates the 4 variable edge lengths - 1 for the simplest S4A4 case of
    folded heptagons.
    
    The case contains
    x[0]: a translation (towards the viewer)
    x[1]: half the angle between the 2 heptagons 0,1,2,3,4,5,6 and 7,8,9,3,4,10,11
    x[2]: the angle of the first fold around 2-5 (9, 10)
    x[3]: the angle of the first fold around 1-6 (8, 11)
    The vertices are positioned as follows:
    #          19                      18
    #
    #
    #             16                14
    #                      12
    #
    #               9             2
    #      8                               1
    #
    #                      3
    #                       
    #   7                                     0
    #                       
    #                      4
    #                       
    #     11                               6
    #              10             5
    #                      
    #                      13
    #             17                15

    And the relevant vertices are defined as follows:
    [ x1,    y1,    z1], # V1
    [ x2,    y2,    z2], # V2
    [ x3,    y3,    z3], # V3

    [-x2,    y2,    z2], # V9 = V2'

    [ y0,    z0,    x0], # V12 = V0'

    [ y1,    z1,    x1], # V14 = V1'

    The heptagons are regular, so 
    |0-1| = |1-2| = |2-3| = |3-4| = |4-5| = |5-6| = |6-0| = |12 - 14| = 1
    The alternatives for creatings triangles leads to the following possible
    variable edge lengths:
    params[0] | edge a | edge b | edge c | edge d 
    ----------+--------+--------+--------+-------
           0  | 2 - 9  | 12 - 2 | 2 - 14 | 14 - 1	strip 1 loose
    ----------+--------+--------+--------+-------
           1  | 3 - 12 | 12 - 2 | 2 - 14 | 14 - 1	strip I
    ----------+--------+--------+--------+-------
           2  | 3 - 12 | 3 - 14 | 2 - 14 | 14 - 1	strip II
    ----------+--------+--------+--------+-------
           3  | 3 - 12 | 12 - 2 | 12 - 1 | 14 - 1	star
    ----------+--------+--------+--------+-------
           4  | 2 - 9  | 12 - 2 | 12 - 1 | 14 - 1	star 1 loose
    ----------+--------+--------+--------+-------
           5  | 2 - 9  | 12 - 2 | 2 - 14 | 18 - 2	strip 1 loose
    ----------+--------+--------+--------+-------
           6  | 3 - 12 | 3 - 14 | 2 - 14 | 18 - 2	alt strip II
    ----------+--------+--------+--------+-------
           7  | 3 - 12 | 12 - 2 | 2 - 14 | 18 - 2	alt strip I

    For the param[0] the following constant names can be used, see TriangleAlt.

    params[1] steers which the edge lengths. It is a vector of 4 floating point
    numbers that expresses the edge lengths of [a, b, c, d]. If params 1 is not
    given, the edge lengths are supposed to be 1.

    params[2] defines which folding method is used.
    """

    T     = x[0]
    alpha = x[1]
    beta  = x[2]
    gamma = x[3]

    #faster = True
    if (faster):
	# this code I wrote first only for the parallel case.
	# I didn't remove the code since it so much faster then the newer code.
	assert params[2] == Fold.parallel, 'Only parallel case is supported for faster mode'
	cosa = numx.cos(alpha)
	sina = numx.sin(alpha)
	cosb = numx.cos(beta)
	sinb = numx.sin(beta)
	cosg = numx.cos(gamma)
	sing = numx.sin(gamma)

	x0__ = cosg * (H) + SigmaH + RhoH
	z0__ = sing * (H)

	x0_  = cosb * (x0__ - RhoH) - sinb * (z0__       ) + RhoH
	z0_  = cosb * (z0__       ) + sinb * (x0__ - RhoH)

	x1_  = cosb * (SigmaH) + RhoH
	z1_  = sinb * (SigmaH)

	x0  = sina * x0_ - cosa * z0_
	x1  = sina * x1_ - cosa * z1_
	x2  = sina * RhoH
	x3  = 0

	y0  =  0.0
	y1  =  Rho / 2
	y2  =  Sigma / 2
	y3  =  1.0 / 2

	z0  = T - (sina * z0_ + cosa * x0_)
	z1  = T - (sina * z1_ + cosa * x1_)
	z2  = T - cosa * (         RhoH)
	z3  = T
    else:
	# rotation angle around edge
	alpha = alpha 
	alpha = alpha - numx.pi/2
	Vs = [
		GeomTypes.Vec([ (1 + Sigma + Rho)*H,      0.0, 0.0]),
		GeomTypes.Vec([     (Sigma + Rho)*H,    Rho/2, 0.0]),
		GeomTypes.Vec([             (Rho)*H,  Sigma/2, 0.0]),
		GeomTypes.Vec([                 0.0,      0.5, 0.0]),
		GeomTypes.Vec([                 0.0,-     0.5, 0.0]),
		GeomTypes.Vec([             (Rho)*H,- Sigma/2, 0.0]),
		GeomTypes.Vec([     (Sigma + Rho)*H,-   Rho/2, 0.0]),
	    ]
	# fold edge:
	# rotate alpha
	a = Vs[4] - Vs[3]
	r = quatRot(a, alpha)
	v0 = rotate(Vs[0] - Vs[3], r) + Vs[3]
	v1 = rotate(Vs[1] - Vs[3], r) + Vs[3]
	v2 = rotate(Vs[2] - Vs[3], r) + Vs[3]
	v3 = Vs[3]
	v5 = GeomTypes.Vec([v2[0], -v2[1], v2[2]])
	v6 = GeomTypes.Vec([v1[0], -v1[1], v1[2]])

	if (params[2] == Fold.parallel):
	    # rotate beta
	    a = v2 - v5
	    r = quatRot(a, beta)
	    v0 = rotate(v0-v2, r) + v2
	    v1 = rotate(v1-v2, r) + v2
	    v6 = rotate(v6-v2, r) + v2
	    # TODO: exchange for this:
	    #v6 = GeomTypes.Vec([v1[0], -v1[1], v1[2]])
	    # rotate gamma
	    a = v1 - v6
	    r = quatRot(a, gamma)
	    v0 = rotate(v0 - v1, r) + v1

	elif (params[2] == Fold.trapezium):
	    # rotate beta
	    a = v6 - v1
	    r = quatRot(a, beta)
	    v0 = rotate(v0-v1, r) + v1
	    # rotate gamma
	    a = v1 - v3
	    r = quatRot(a, gamma)
	    v2 = rotate(v2-v1, r) + v1

	elif (params[2] == Fold.triangle):
	    # rotate gamma
	    a = v0 - v2
	    r = quatRot(a, gamma)
	    v1 = rotate(v1-v0, r) + v0
	    # rotate beta
	    a = v5 - v2
	    r = quatRot(a, beta)
	    v0 = rotate(v0-v2, r) + v2
	    v1 = rotate(v1-v2, r) + v2

	elif (params[2] == Fold.w):
	    # rotate beta
	    a = v0 - v3
	    r = quatRot(a, beta)
	    v1 = rotate(v1-v0, r) + v0
	    v2 = rotate(v2-v0, r) + v0
	    # rotate gamma
	    a = v1 - v3
	    r = quatRot(a, gamma)
	    v2 = rotate(v2-v1, r) + v1

	elif (params[2] == Fold.star):
	    # rotate beta
	    a = v0 - v3
	    r = quatRot(a, beta)
	    v1 = rotate(v1-v0, r) + v0
	    v2 = rotate(v2-v0, r) + v0
	    # rotate gamma
	    a = v0 - v2
	    r = quatRot(a, gamma)
	    v1 = rotate(v1-v0, r) + v0

	x0, y0, z0 = v0
	x1, y1, z1 = v1
	x2, y2, z2 = v2
	x3, y3, z3 = v3
	z0 = z0 + T
	z1 = z1 + T
	z2 = z2 + T
	z3 = z3 + T

    #print 'v0', x0, y0, z0
    #print 'v1', x1, y1, z1
    #print 'v2', x2, y2, z2
    #print 'v3', x3, y3, z3
    y = copy.copy(x)
    edgeAlternative = params[0]
    #
    # EDGE A
    #
    edgeLengths = [1., 1., 1., 1.]
    try:
        edgeLengths = params[1]
    except IndexError:
        pass
    if ((
	    edgeAlternative > TriangleAlt.strip1loose
	    and edgeAlternative < TriangleAlt.star1loose
	) or (
	    edgeAlternative > TriangleAlt.alt_strip1loose
	)
    ):
        # V3 - V12:[ y0,    z0,    x0], # V12 = V0'
        y[0] = numx.sqrt((x3-y0)*(x3-y0) + (y3-z0)*(y3-z0) + (z3-x0)*(z3-x0)) - edgeLengths[0]
    else:
        # V2 - V9:[-x2,    y2,    z2], # V9 = V2'
        y[0] = numx.sqrt(4*x2*x2) - edgeLengths[0]
    #
    # EDGE B
    #
    if (
	edgeAlternative == TriangleAlt.stripII
	or edgeAlternative == TriangleAlt.alt_stripII
    ):
        # V3 - V14:[ y1,    z1,    x1], # V14 = V1'
        y[1] = numx.sqrt((x3-y1)*(x3-y1) + (y3-z1)*(y3-z1) + (z3-x1)*(z3-x1)) - edgeLengths[1]
    else:
        #V2 - V12:[ y0,    z0,    x0], # V12 = V0'
        y[1] = numx.sqrt((x2-y0)*(x2-y0) + (y2-z0)*(y2-z0) + (z2-x0)*(z2-x0)) - edgeLengths[1]
    #
    # EDGE C
    #
    if (
	edgeAlternative < TriangleAlt.star
	or edgeAlternative > TriangleAlt.star1loose
    ):
        # V2 - V14:[ y1,    z1,    x1], # V14 = V1'
        y[2] = numx.sqrt((x2-y1)*(x2-y1) + (y2-z1)*(y2-z1) + (z2-x1)*(z2-x1)) - edgeLengths[2]
    else:
        # V1 - V12:[ y0,    z0,    x0], # V12 = V0'
        y[2] = numx.sqrt((x1-y0)*(x1-y0) + (y1-z0)*(y1-z0) + (z1-x0)*(z1-x0)) - edgeLengths[2]
    #
    # EDGE D
    #
    if (edgeAlternative < TriangleAlt.alt_strip1loose):
	y[3] = numx.sqrt((x1-y1)*(x1-y1) + (y1-z1)*(y1-z1) + (z1-x1)*(z1-x1)) - edgeLengths[3]
    else:
        # V2 - V18:[ y2,    z2,    x2], # V18 = V2'
	y[3] = numx.sqrt((x2-y2)*(x2-y2) + (y2-z2)*(y2-z2) + (z2-x2)*(z2-x2)) - edgeLengths[3]

    #print y
    return y

class Method:
    hybrids = 0
    dnewton = 1
    broyden = 2
    hybrid  = 3

def FindMultiRoot(initialValues, 
        edgeAlternative,
        edgeLengths = [1., 1., 1., 1.],
	fold = Fold.parallel,
        method = 1,
        cleanupF  = None,
        precision = 1e-15,
        maxIter = 100,
        printIter = False,
        quiet     = False,
    ):
    if not quiet:
        print '[|a|, |b|, |c|, |d|] =', edgeLengths, 'for',
        if edgeAlternative == 0:
            print 'triangle strip, 1 loose:'
        elif edgeAlternative == 1:
            print 'triangle strip I:'
        elif edgeAlternative == 2:
            print 'triangle strip II:'
        elif edgeAlternative == 3:
            print 'triangle star:'
        elif edgeAlternative == 4:
            print 'triangle star, 1 loose:'

    mysys = multiroots.gsl_multiroot_function(
        FoldedRegularHeptagonsS4A4,
        [edgeAlternative, edgeLengths, fold],
        4
    )
    
    nrOfIns = 4
    if method == Method.hybrids:
        solver = multiroots.hybrids(mysys, nrOfIns)
    elif method == Method.dnewton:
        solver = multiroots.dnewton(mysys, nrOfIns)
    elif method == Method.broyden:
        solver = multiroots.broyden(mysys, nrOfIns)
    else:
        solver = multiroots.hybrid(mysys, nrOfIns)
    
    solver.set(initialValues)
    if printIter:
        print "# Using solver ", solver.name(), 'with edge alternative:', edgeAlternative
        print "# %5s %9s %9s %9s %9s  %9s  %10s  %9s  %10s" % (
            "iter",
            "x[0]", "x[1]", "x[2]", "x[3]",
            "f[0]", "f[1]", "f[2]", "f[3]"
        )
        # Get and print initial values
        r = solver.root()
        x = solver.getx()
        f = solver.getf()
        print "  %5d % .7f % .7f % .7f % .7f  % .7f  % .7f  % .7f  % .7f" %(
            0,
            x[0], x[1], x[2], x[3],
            f[0], f[1], f[2], f[3]
        )
    result = None
    for iter in range(maxIter):
        status = solver.iterate()
        r = solver.root()
        x = solver.getx()
        f = solver.getf()
        status = multiroots.test_residual(f, precision)
        if status == errno.GSL_SUCCESS and not quiet:
            print "# Converged :"
        if printIter:
            print "  %5d % .7f % .7f % .7f % .7f  % .7f  % .7f  % .7f  % .7f" %(
                iter+1,
                x[0], x[1], x[2], x[3],
                f[0], f[1], f[2], f[3]
            )
        if status == errno.GSL_SUCCESS:
            # Now print solution with high precision
            if not quiet:
                for i in range(nrOfIns):
                    print "x[%d] = %.15f" % (i, x[i])
            result = [x[i] for i in range(nrOfIns)]
            break
    else:
        if not quiet:
            print "# not converged... :("
    if result != None and cleanupF != None:
        result = cleanupF(result)
    return result

# This can be optimised
def solutionAlreadyFound(sol, list, precision = 1.e-12):
    found = False
    lstRange = range(len(sol))
    for old in list:
        allElemsEqual = True
        for i in lstRange:
            if abs(old[i] - sol[i]) > precision:
                allElemsEqual = False
                break # for i loop, not for old
        if allElemsEqual:
            found = True
            break # for old loop
    return found

def FindMultiRootOnDomain(domain,
        edgeAlternative,
        edgeLengths = [1., 1., 1., 1.],
	fold = Fold.parallel,
        method = 1,
        cleanupF  = None,
        stepSize = 0.1, # TODO make this an array to allow different stepsizes for different parameters
        precision = 1e-15,
        maxIter = 100,
	continueTestAt = None,
	init_results = [],
	printStatus = False
    ):
    results = init_results[:]
    dLen = len(domain)
    if (continueTestAt == None):
	testValue = [domain[i][0] for i in range(dLen)]
    else:
	testValue = continueTestAt[:]
	print 'continuing search...'
    if printStatus:
	print testValue
    while testValue[-1] < domain[-1][1]:
    #while testValue[0] < domain[0][1]:
        try:
            result = FindMultiRoot(testValue, 
                    edgeAlternative,
                    edgeLengths,
		    fold,
                    method,
                    cleanupF,
                    precision,
                    maxIter,
                    printIter = False,
                    quiet     = True,
                )
            if result != None and not solutionAlreadyFound(result, results):
                results.append(result)
                print 'added new result nr', len(results),':', result
        except pygsl.errors.gsl_SingularityError:
            pass
        except pygsl.errors.gsl_NoProgressError:
            pass
        except pygsl.errors.gsl_JacobianEvaluationError:
            pass
        #for i in range(dLen-1, 0, -1):
        for i in range(dLen):
            # note that domain[i][1] is not tested if the steps do not end there
            # explicitely. TODO also test upper limits.
            testValue[i] += stepSize
            if testValue[i] <= domain[i][1]:
                break # break from for-loop, not from while
            else:
                if i != dLen-1:
                    testValue[i] = domain[i][0]
		if printStatus:
		    print testValue
    return results

if __name__ == '__main__':
    #tmp = numx.array((0.0, 1.57, 0.00, 0.00))
    #faster = False
    #FoldedRegularHeptagonsS4A4(tmp, [0])
    faster = False
    #FoldedRegularHeptagonsS4A4(tmp, [0])
    #tmp = numx.array((1.1789610329092914, 0.69387894107538728, 2.1697959367422728, -0.49295326187544664))
    #tmp = numx.array((0.00, 0.00, 0.00, 0.00))
    #print FoldedRegularHeptagonsS4A4(tmp,
    #    [TriangleAlt.strip1loose, [0., 0., 0., 0.], Fold.star ])

    #blabla

    V2 = numx.sqrt(2.)

    tpi = 2*numx.pi
    def cleanupResult(v):
        for i in range(1,4):
            v[i] = v[i] % tpi
            if v[i] > numx.pi:
                v[i] -= tpi
        return v

    FindSingleRoots = False
    if FindSingleRoots:
        #
        # EDGE LENGTH [1, 1, 1, 0]
        #
        # Triangle strip 1 loose
        #FindMultiRoot(
        #    initialValues   = numx.array((2.4, 0.69,  0.28, 0.07)),
        #    edgeAlternative = TriangleAlt.strip1loose,
        #    edgeLengths     = [1., 1., 1., 0.],
        #    method          = Method.hybrids
        #    #precision       = 1.0e-11,
        #    #maxIter         = 1000
        #)

        # Triangle strip I
        #FindMultiRoot(
        #    initialValues   = numx.array((2.3, 1.03,  0.79, -0.76)),
        #    edgeAlternative = TriangleAlt.stripI,
        #    edgeLengths     = [1., 1., 1., 0.],
        #)

        #
        # EDGE LENGTH [1, 1, 1, 1]
        #
        # Triangle strip 1 loose
        #FindMultiRoot(
        #    initialValues   = numx.array((2.7, 0.70, -0.45,  1.48)),
        #    edgeAlternative = TriangleAlt.strip1loose
        #)
        #FindMultiRoot(
        #    initialValues   = numx.array((1.5, 2.44, 1.27, -0.91)),
        #    edgeAlternative = TriangleAlt.strip1loose
        #)

        # Triangle strip I
        #FindMultiRoot(
        #    initialValues   = numx.array((2.2, 1.75, 0.91, 0.0)),
        #    edgeAlternative = TriangleAlt.stripI
        #)
        #FindMultiRoot(
        #    initialValues   = numx.array((0.3, 2.09,  0.26, 2.82)),
        #    edgeAlternative = TriangleAlt.stripI
        #)
        #FindMultiRoot(
        #    initialValues   = numx.array((1.6, 0.93,  0.65, 2.67)),
        #    edgeAlternative = TriangleAlt.stripI
        #)

        # Triangle star
        #FindMultiRoot(
        #    initialValues   = numx.array((1.7, 0.56, -1.59,  0.71)),
        #    edgeAlternative = TriangleAlt.star,
        #    #method          = Method.hybrids
        #)

        # Triangle star, 1 loose
        #FindMultiRoot(
        #    # not good enough, but converges ~ to next values:
        #    #initialValues   = numx.array((3.1, 0.66,  0.00,  0.00)),
        #    initialValues   = numx.array((1.7, 0.69,  0.80, -2.18)),
        #    edgeAlternative = TriangleAlt.star1loose,
        #    edgeLengths     = [1., 1., 1., 1.],
        #    #method          = Method.hybrids
        #)

        # Triangle star, 1 loose
        #FindMultiRoot(
        #    initialValues   = numx.array((1.7, 0.56, -1.59,  0.71)),
        #    edgeAlternative = TriangleAlt.star1loose,
        #    #method          = Method.hybrids
        #)

        #
        # EDGE LENGTH [1, 1, 0, 1]
        #
        # Triangle strip II
        # Not possible
        #FindMultiRoot(
        #    initialValues   = numx.array((1.5, 1.62, 0.42, -0.61)),
        #    edgeAlternative = TriangleAlt.stripII,
        #    edgeLengths     = [1., 1., 0., 1.],
        #    #method          = Method.hybrids
        #)

        #
        # EDGE LENGTH [V2, 1, 1, 1]
        #
        # Triangle star, 1 loose
        #FindMultiRoot(
        #    initialValues   = numx.array((1.4, 1.13, -1.90,  1.74)),
        #    edgeAlternative = TriangleAlt.star1loose,
        #    edgeLengths     = [V2, 1., 1., 1.],
        #    method          = Method.hybrids
        #)

        #
        # EDGE LENGTH [1, V2, 1, 0]
        #
        #FindMultiRoot(
        #    # doesn't converge:
        #    initialValues   = numx.array((1.9, 1.50,  1.38,  0.00)),
        #    edgeAlternative = TriangleAlt.stripII,
        #    edgeLengths     = [1., V2, 1., 0.],
        #    #method          = Method.hybrids
        #)

        #
        # EDGE LENGTH [1, 1, V2, 1]
        #
        # Triangle star
        #FindMultiRoot(
        #    initialValues   = numx.array((1.4, 1.13, -1.38,  1.64)),
        #    edgeAlternative = TriangleAlt.star,
        #    edgeLengths     = [1., 1., V2, 1.],
        #    #method          = Method.hybrids
        #)

        # Triangle strip II
        #FindMultiRoot(
        #    initialValues   = numx.array((-0.2, 2.90,  1.55, 2.50)),
        #    edgeAlternative = TriangleAlt.star,
        #    edgeLengths     = [1., 1., V2, 1.],
        #    #method          = Method.hybrids
        #)

        #
        # EDGE LENGTH [1, 1, 0, 1]
        #
        # Triangle strip II
        #FindMultiRoot(
        #    initialValues   = numx.array((-0.2, 2.90,  1.55, 2.50)),
        #    edgeAlternative = TriangleAlt.star,
        #    edgeLengths     = [1., 1., 0, 1.],
        #    #method          = Method.hybrids
        #)

        #
        # EDGE LENGTH [0, 0, 1, 0]
        #
        # Triangle strip 1 loose
        #FindMultiRoot(
        #    initialValues   = numx.array((2.3, 0.75, -1.05, 0.09)),
        #    #initialValues   = numx.array((2.3, 0.70, -0.93, -1.06)),
        #    #edgeAlternative = TriangleAlt.strip1loose,
        #    #edgeAlternative = TriangleAlt.stripI,
        #    edgeAlternative = TriangleAlt.star1loose,
        #    edgeLengths     = [0., 0., 1., 0.],
	#    fold            = Fold.w,
        #    #method          = Method.hybrids
        #)
	# NOTE, with the settings above nothing is found. Something is found
	# though by using the same settings, but another triangle alternative.
	# This is also a solution for the above...
	# NOTE NOTE NOTE
	# This means that it is likely that the digital search in the else
	# clause below misses local solutions (which I was already afraid of)
        #FindMultiRoot(
        #    initialValues   = numx.array((2.3, 0.75, -1.05, 0.09)),
        #    #initialValues   = numx.array((2.3, 0.70, -0.93, -1.06)),
        #    #edgeAlternative = TriangleAlt.strip1loose,
        #    edgeAlternative = TriangleAlt.star,
        #    edgeLengths     = [1., 0., 1., 0.],
	#    fold            = Fold.w,
        #    #method        heightF  = Method.hybrids
        #)

	# no conversion:
        #FindMultiRoot(
        #    initialValues   = numx.array((2.3, 0.63,  1.08, -0.99)),
        #    edgeAlternative = TriangleAlt.star,
        #    edgeLengths     = [1., 0., 1., 0.],
	#    fold            = Fold.trapezium,
        #    #method          = Method.hybrids
        #)

	# no conversion:
        #FindMultiRoot(
        #    initialValues   = numx.array((1.3, 1.40, -2.06,  0.99)),
        #    edgeAlternative = TriangleAlt.stripI,
        #    edgeLengths     = [0., 1., 0., 1.],
	#    fold            = Fold.trapezium,
        #    #method          = Method.hybrids
        #)

        #
        # EDGE LENGTH [1, 1, 2, 1]
        # C will be shared by 2 edges
        # Triangle star
        # no solutions
        #FindMultiRoot(
        #    initialValues   = numx.array((1.6, 1.47,  0.00,  0.09)),
        #    edgeAlternative = TriangleAlt.stripII,
        #    edgeLengths     = [1., 1., 2., 1.],
        #    #method          = Method.hybrids
        #)

        #FindMultiRoot(
        #    # doesn't converge:
        #    #initialValues   = numx.array((2.1, 1.20,  1.05,  0.49)),
        #    # doesn't converge:
        #    initialValues   = numx.array((2.3, 0.79,  0.35, -1.24)),
        #    edgeAlternative = TriangleAlt.stripII,
        #    edgeLengths     = [1., 1., 1., 0.],
        #    printIter = True,
        #    #method          = Method.hybrids
        #)

        #FindMultiRoot(
        #    # doesn't converge:
        #    #initialValues   = numx.array((2.1, 1.20,  1.05,  0.49)),
        #    # doesn't converge:
        #    initialValues   = numx.array((2.5, 0.51, 2.97, -1.43)),
        #    edgeAlternative = TriangleAlt.strip1loose,
        #    edgeLengths     = [0., 1., 1., 0.],
	#    fold            = Fold.trapezium,
        #    #printIter = True,
        #    #method          = Method.hybrids
        #)

        #FindMultiRoot(
        #    # doesn't converge:
        #    #initialValues   = numx.array((1.7, 1.45, -0.72,  0.75)),
        #    #initialValues   = numx.array((1.8, 1.2, -0.38,  0.94)),
        #    initialValues   = numx.array((1.75, 1.32, -0.50,  0.84)),
        #    #edgeAlternative = TriangleAlt.stripI,
        #    edgeAlternative = TriangleAlt.stripII,
        #    edgeLengths     = [0., 1., 0., 1.],
	#    fold            = Fold.triangle,
        #    #printIter = True,
        #    #method          = Method.hybrids
        #)

        #FindMultiRoot(
        #    # doesn't converge:
        #    initialValues   = numx.array((2.00, 1.06,  0.58,  0.12)),
	#    edgeAlternative = TriangleAlt.stripI,
	#    edgeLengths = [1., 1., 0., 1.],
	#    fold = Fold.trapezium,
        #    #printIter = True,
        #    #method          = Method.hybrids
        #)

        #FindMultiRoot(
        #    # doesn't converge:
        #    initialValues   = numx.array((2.10, 1.29, -0.63, -0.37)),
	#    edgeAlternative = TriangleAlt.stripI,
	#    edgeLengths = [1., 1., 0., 1.],
	#    fold = Fold.star,
        #    #printIter = True,
        #    #method          = Method.hybrids
        #)

        #FindMultiRoot(
        #    # YES
        #    initialValues   = numx.array((2.40, 0.72, -0.98, -1.34)),
	#    edgeAlternative = TriangleAlt.star,
	#    edgeLengths = [1., 0., 1., 1.],
	#    fold = Fold.star,
        #    #printIter = True,
        #    #method          = Method.hybrids
        #)

        #FindMultiRoot(
        #    # doesn't converge:
	#    # taken from 1, 1, 0, 1
        #    initialValues   = numx.array((1.240760438271816, 1.4093511342004652, 0.64591225448264056, -1.2296559797224518)),
	#    edgeAlternative = TriangleAlt.stripI,
	#    edgeLengths = [V2, 1., 0., 1.],
	#    fold = Fold.star,
        #    #printIter = True,
        #    #method          = Method.hybrids
        #)

	pass
    else:
        Domain = [
                [-2., 3.],           # Translation
                [-numx.pi, numx.pi], # angle alpha
                [-numx.pi, numx.pi], # fold 1 beta
                [-numx.pi, numx.pi], # fold 2 gamma
            ]

	def batch(fold, edges, tris):
	    print 'searching %s folds' % str(fold)
	    result = []
	    result = FindMultiRootOnDomain(Domain,
		    edgeLengths = edges,
		    edgeAlternative = tris,
		    fold = fold.fold,
		    method = Method.hybrids,
		    cleanupF = cleanupResult,
		    stepSize = 0.3,
		    maxIter = 20
		)
	    print '['
	    for r in result: print '  %s,' % str(r)
	    print '],'

	#edges = [0., 1., 0., 1.]
	#tris = TriangleAlt.strip1loose # done
	#tris = TriangleAlt.star # TODO
	#tris = TriangleAlt.star1loose # TODO
	#tris = TriangleAlt.stripI # TODO REDO

	#edges = [0., 1., 1., 0.]
	#tris = TriangleAlt.alt_stripII # done

	edges = [1., 0., 1., 0.]
	#tris = TriangleAlt.alt_stripII # done
	tris = TriangleAlt.alt_stripI #

	print edges, Stringify[tris], 'triangle alternative'
	fold.set(fold.parallel)
	batch(fold, edges, tris)
	fold.set(fold.triangle)
	batch(fold, edges, tris)
	fold.set(fold.star)
	batch(fold, edges, tris)
	fold.set(fold.w)
	batch(fold, edges, tris)
	fold.set(fold.trapezium)
	batch(fold, edges, tris)

	#print 'V2, 1, 1, 0, star1loose'
	#fold.set(fold.star)
	#batch2(fold)
	#fold.set(fold.w)
	#batch2(fold)
	#fold.set(fold.triangle)
	#batch2(fold)
	#fold.set(fold.trapezium)
	#batch2(fold)
	#fold.set(fold.parallel)
	#batch2(fold)

