#! /usr/bin/python
#
# Copyright (C) 2010 Marcel Tunnissen
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
# -----------------------------------------------------------------
from __future__ import print_function

import isometry


class Orbit(list):
    def __new__(this, v):
        assert len(v) == 2
        assert isinstance(v[0], isometry.Set)
        assert isinstance(v[1], isometry.Set)
        this.final = v[0]
        this.stabiliser = v[1]
        return list.__new__(this, v)

    def __repr__(v):
        s = '%s([\n'
        s = '%s  %s\n' % repr(v[0])
        s = '%s  %s\n' % repr(v[1])
        s = '%s])\n'
        if __name__ != '__main__':
            s = '%s.%s' % (__name__, s)
        return s

    def __str__(v):
        s = '%s([\n'
        s = '%s  final = %s\n' % str(v[0])
        s = '%s  stabiliser = %s\n' % str(v[1])
        s = '%s])\n'
        if __name__ != '__main__':
            s = '%s.%s' % (__name__, s)
        return s

    @property
    def higherOrderStabiliserProps(v):
        """Get possible sub orbit classes for higher order stabilisers

        A higher order stabiliser is a subgroup of G that has the stabiliser as
        a subgroup. Practically this is used for colouring
        of polyhedra. E.g. The polyhedra is defined by one face with some
        symmetry. Then the higher order stabiliser is the set of faces with the
        same colour. The groups of different coloured faces are mapped onto
        each other by the orbit that is derived from the higher order
        stabiliser. This orbit is a sub-orbit of the original orbit. The norm
        of this sub-orbit equals to the amount of colours used.
        Returns: a list of dictionaries with properties of higher order
        stabilisers. Each dictionary holds:
            'class': higher order stabiliser classes is obtained.
            'index': the length of the subgroups in the final group, or the
                     norm of the coset.
        """
        try:
            assert v.__hospCalled, 'if this exists it should be true'
        except AttributeError:
            v.__hosProps = v.__hosp()
            v.__hospCalled = True
        return v.__hosProps

    def __hosp(v):
        """See higherOrderStabiliserProps"""
        higherOrderStabiliserProps = []
        v.hoStabs = []
        v.indexCovered = {}
        for subGroup in v.final.subgroups:
            assert subGroup.order != 0, "{} ({})".format(
                (str(subGroup),
                 subGroup.__class__.__name__))
            if v.stabiliser.__class__ in subGroup.subgroups:
                # Check if the stabiliser can really be a subgroup for this
                # orientation.
                # E.g.
                # final symmetry S4xI
                # stabiliser: D2C2 with principle axis: one 2-fold from S4xI
                #                                       (ie not a 4-fold axis)
                # Now A4xI is a subgroup of S4xI
                # and D2C2 is a subgroup of A4xI,
                # However the D2C2 that is a subgroup of the A4xI subgroup of
                # S4xI has a principle axis that is a 4-fold axis of S4xI.

                hoStabs = v.final.realise_subgroups(subGroup)
                # from end to beginning, because elements will be filtered out:
                for i in range(len(hoStabs)-1, -1, -1):
                    if v.stabiliser.is_subgroup(hoStabs[i]):
                        break
                    else:
                        # remove this from the list, this is part of the work
                        # of filtering the list. This is not done completely
                        # here since it costs time, and the user might not
                        # choose this sub orbit anyway (hence the break above).
                        # But to save time later, remove it already.
                        del hoStabs[i]
                index = v.final.order/subGroup.order
                if hoStabs:
                    higherOrderStabiliserProps.append({'class': subGroup,
                                                       'index': index,
                                                       'filtered': i})
                    v.hoStabs.append(hoStabs)
                    v.indexCovered[index] = True
                # else filter out, since no real subgroup
            # else: this subgroup of G doesn't have the stabiliser as subgroup
        return higherOrderStabiliserProps

    def higherOrderStabiliser(v, n):
        """Get possible sub orbits for higher order stabilisers

        With this a list of higher order stabilisers of one class is obtained.
        n: the list index in higherOrderStabiliserProps representing the class.
        see also higherOrderStabiliserProps.
        """

        # Make sure the list is initialised.
        props = v.higherOrderStabiliserProps

        # filter rest if needed:
        if not props:
            return []
        if (props[n]['filtered'] > 0):
            # Now filter out the stabilisers that are not a subgroup for this
            # orientation.
            # (part of this is done in __hosp)
            # E.g.
            # final symmetry S4xI
            # stabiliser: D2C2 with principle axis: one 2-fold from S4xI
            #                                       (ie not a 4-fold axis)
            # Now D4xI is a subgroup of S4xI
            # and D2C2 is a subgroup of D4xI,
            # but not necessarily this orientation. In fact only one of the
            # three possible D4xI will have this D2C2 as subgroup.
            for i in range(props[n]['filtered']-1, -1, -1):
                if not v.stabiliser.is_subgroup(v.hoStabs[n][i]):
                    del v.hoStabs[n][i]
            assert len(v.hoStabs[n]) != 0, (
                "This case should have been checked in __hosp"
            )
            props[n]['filtered'] = 0
        return v.hoStabs[n]

    @property
    def lowerOrderStabiliserProps(v):
        """Get possible sub orbit classes for lower order stabilisers

        Lower order stabiliser are very similar to higher order stabiliser.
        These are called lower, since they are lower than higher. For groups
        that have both direct and opposite isometries only the direct
        isometries are considered. Then for this only-direct stabiliser and the
        only-direct final group the higher order stabilisers are generated.

        The same list of dictionaries is returned as in
        higherOrderStabiliserProps
        """
        try:
            assert v.__lospCalled, 'if this exists it should be true'
        except AttributeError:
            v.__losProps = v.__losp()
            v.__lospCalled = True
        return v.__losProps

    def __losp(v):
        """See lowerOrderStabiliserProps"""

        lowerOrderStabiliserProps = []
        v.loStabs = []
        # if stabiliser has both direct and opposite isometries
        if v.stabiliser.mixed:
            # alternative way of colouring by using the direct parents; i.e.
            # the parent with only direct isometries
            assert v.final.mixed
            if v.final.generator:
                v.altFinal = v.final.direct_parent(
                        setup=v.final.direct_parent_setup)
            else:
                v.altFinal = v.final.direct_parent(
                    isometries=[isom for isom in v.final if isom.is_direct()])
            if v.stabiliser.generator:
                v.altStab = v.stabiliser.direct_parent(
                    setup=v.stabiliser.direct_parent_setup)
            else:
                v.altStab = v.stabiliser.direct_parent(
                    isometries=[
                        isom for isom in v.stabiliser if isom.is_direct()])

            # TODO: fix; don't copy above code from hosp__
            for subGroup in v.altFinal.subgroups:
                assert subGroup.order != 0
                if v.altStab.__class__ in subGroup.subgroups:
                    loStabs = v.altFinal.realise_subgroups(subGroup)
                    for i in range(len(loStabs)-1, -1, -1):
                        if v.altStab.is_subgroup(loStabs[i]):
                            break
                        else:
                            del loStabs[i]
                    index = v.altFinal.order/subGroup.order
                    try:
                        if v.indexCovered[index]:
                            pass
                    except KeyError:
                        if loStabs != []:
                            lowerOrderStabiliserProps.append({
                                    'class': subGroup,
                                    'index': index, 'filtered': i
                                }
                            )
                            v.loStabs.append(loStabs)
                            # don't add to v.indexCovered, it means covered by
                            # __hosp, really

        return lowerOrderStabiliserProps

    def lowerOrderStabiliser(v, n):
        """Get possible sub orbits for higher order stabilisers

        With this a list of higher order stabilisers of one class is obtained.
        n: the list index in lowerOrderStabiliserProps representing the class.
        see also lowerOrderStabiliserProps.
        """

        # Make sure the list is initialised.
        props = v.lowerOrderStabiliserProps

        # filter rest if needed:
        if (props[n]['filtered'] > 0):
            for i in range(props[n]['filtered']-1, -1, -1):
                if not v.altStab.is_subgroup(v.loStabs[n][i]):
                    del v.loStabs[n][i]
            assert len(v.loStabs[n]) != 0, (
                "This case should have been checked in __losp"
            )
            props[n]['filtered'] = 0
        return v.loStabs[n]
