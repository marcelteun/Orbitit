from __future__ import print_function

import math
import os

import GeomTypes
import Geom3D
import isometry
import orbit

col_red = [1, 0, 0]
col_yellow = [1, 1, 0]
col_green = [0, 1, 0]

if False:
    Vs = [
        GeomTypes.Vec3([1, 1, 1]),
        GeomTypes.Vec3([-1, -1, 1]),
        GeomTypes.Vec3([1, -1, -1]),
        GeomTypes.Vec3([-1, 1, -1])
    ]
    Fs = [
        [0, 2, 1],
        [0, 1, 3],
        [0, 3, 2],
        [2, 3, 1]
    ]

    final_sym = isometry.S4(
        setup={'o4axis0': GeomTypes.Vec3([1.0, 0.0, 0.0]),
               'o4axis1': GeomTypes.Vec3([0.0, 1.0, 0.0])})
    stab_sym = isometry.C2(
        setup={'n': 2,
               'axis': GeomTypes.Vec3([0.0, 0.0, 1.0])})
    col_sym = isometry.D4
    col_alt = 2
    cols = [col_red, col_yellow, col_green]
else:
    Vs = [
        GeomTypes.Vec3([0, 0, 0]),
        GeomTypes.Vec3([2, 2, 2]),
        GeomTypes.Vec3([2, 0, 2]),
        GeomTypes.Vec3([2, -2, 2]),
        GeomTypes.Vec3([0, -2, 2]),
        GeomTypes.Vec3([-2, -2, 2]),
        GeomTypes.Vec3([-2, 0, 2]),
        GeomTypes.Vec3([-2, 2, 2]),
        GeomTypes.Vec3([0, 2, 2]),
    ]
    Fs = [
        [0, 2, 1],
        [0, 1, 3],
        [0, 3, 2],
        [2, 3, 1]
    ]
    final_sym = isometry.S4xI(
        setup={'o4axis0': GeomTypes.Vec3([1.0, 0.0, 0.0]),
               'o4axis1': GeomTypes.Vec3([0.0, 1.0, 0.0])})
    stab_sym = isometry.C4(
        setup={'n': 4,
               'axis': GeomTypes.Vec3([0.0, 0.0, 1.0])})
    col_sym = isometry.S4
    col_alt = 0
    cols = [col_red, col_yellow]

sym_shape = Geom3D.SymmetricShape(
    Vs, Fs,
    finalSym=final_sym,
    stabSym=stab_sym)

# TODO: move into class SymShape
sym_shape.orbit = orbit.Orbit((final_sym, stab_sym))
sym_shape.no_of_col_opts = {
    p['class']: {'order': p['index'], 'index': i}
    for i, p in enumerate(sym_shape.orbit.higherOrderStabiliserProps)
}
# TODO handle lower order later
# sym_shape.no_of_col_opts.extend([
#     {'no_of_cols': p['index'], 'class': p['class']}
#     for p in sym_shape.orbit.lowerOrderStabiliserProps
# ])


def select_col_sym_opt(sym_shape, name):
    """Select on what symmetry the colouring shall be based

    sym_shape: symmetry shape object
    name: symmetry class that should be a higher order stability. I.e. the
          stabiliser symmetry should be a subgroup of this group and this group
          should be a subgroup of the final symmetry
    return: amount of alternatives for this symmetry
    """
    assert name in sym_shape.no_of_col_opts, \
        "{} not a higher order stabiliser of final symmetry {}".format(
            name, sym_shape.finalSym)
    sym_shape.col_sym_opt = sym_shape.no_of_col_opts[name]['index']
    sym_shape.col_isom_alts = sym_shape.orbit.higherOrderStabiliser(
        sym_shape.col_sym_opt)
    return len(sym_shape.col_isom_alts)


def get_no_of_cols(sym_shape):
    """Get how many colours are needed after calling select_col_sym_opt"""
    return sym_shape.orbit.higherOrderStabiliserProps[sym_shape.col_sym_opt][
        'index']


def select_col_alt(sym_shape, i, cols):
    """Select the colout alternative for the defined colour symmetry option

    i: index, integer from 0 and smaller than the the returned value in
       select_col_sym_opt
    cols: the colours to use, array of length n with rgb values, where n equals
          to the value returned by get_no_of_cols and rgb values are floating
          point values between 0 and 1.
    """
    assert i >= 0, "Colour alternative cannot be negative (got {})".format(i)
    assert i < len(sym_shape.col_isom_alts), \
        "Colour alternative no. should be less than {}, got {}".format(
            len(sym_shape.col_isom_alts), i)
    assert len(cols) == get_no_of_cols(sym_shape), \
        "Wrong no. of colours, got {}, expected {}".format(
            len(cols), get_no_of_cols(sym_shape))
    col_quotient_set = sym_shape.finalSym / sym_shape.col_isom_alts[i]
    col_per_isom = []
    for isom in sym_shape.getIsometries()['direct']:
        for i, subSet in enumerate(col_quotient_set):
            if isom in subSet:
                col_per_isom.append(cols[i])
                break
    cols = [([col], []) for col in col_per_isom]
    sym_shape.setFaceColors(cols)


select_col_sym_opt(sym_shape, col_sym)
select_col_alt(sym_shape, col_alt, cols)

orbit_str = sym_shape.export_as_orbit([0, math.pi/8, math.pi/4],
                                      [0, 0, 1],
                                      prec=9)
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                       "tetras.orbit"), 'r') as fd:
    # remove EOF:
    content = fd.read()[:-1]
    if content != orbit_str:
        print('Ooops strings not equal:')
        for l1, l2 in zip(content, orbit_str):
            assert l1 == l2, '{} != {}'.format(l1, l2)

print('All tests passed')
