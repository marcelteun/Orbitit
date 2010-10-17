#! /usr/bin/python

import math
#import re
import GeomTypes
import isometry
#from copy import copy

def setup(**kwargs): return kwargs

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

        A sub-orbit is used if a group of isometries are used on the
        stabiliser to obtain a higher order stabiliser. This higher order
        stabiliser requires a sub orbit. Practically this is used for colouring
        of polyhedra. E.g. The polyhedra is defined by one face with some
        symmetry. Then the higher order stabiliser is the set of faces with the
        same colour. SUch a set has there own symmetry. The different groups of
        coloured faces are mapped onto each other by a sub orbit. The norm of
        this sub-orbit equals to the amount of colours used. With this a list of
        dictionaries is obtained. Each dictionary holds:
            'class': higher order stabiliser classes is obtained.
            'index': the length of the subgroups in the final group, or the
                     norme of the coset.
        """
        try:
            assert v.__hoscCalled == True, 'if this exists it should be true'
        except AttributeError:
            v.__hosProps = v.__hosp()
            v.__hosPropsCalled = True
        #print 'higherOrderStabiliserProps', v.__hosProps
        return v.__hosProps


    def __hosp(v):
        """See higherOrderStabiliserProps"""

        #print '%s.getSubOrbitClasses' % v.__class__.__name__
        higherOrderStabiliserProps   = []
        v.hoStabs                    = []
        v.indexCovered               = {}
        for subGroup in v.final.subgroups:
            #print 'subGroup', subGroup.__class__.__name__
            #print '...contains stabiliser', v.stabiliser, '...??..',
            assert subGroup.order != 0
            if v.stabiliser.__class__ in subGroup.subgroups:
                #print 'yes'

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

                hoStabs = v.final.realiseSubgroups(subGroup)
                #print 'check list of len:', len(hoStabs)
                # from end to beginning, because elements will be filtered out:
                for i in range(len(hoStabs)-1, -1, -1):
                    #print 'isSubgroup', v.stabiliser, hoStabs[i]
                    if v.stabiliser.isSubgroup(hoStabs[i]):
                        #print 'yes, break at index', i
                        break
                    else:
                        # remove this from the list, this is part of the work of
                        # filtering the list. This is not done completely here
                        # since it costs time, and the user might not choose
                        # this sub orbit anyway (hence the break above). But to
                        # save time later, remove it already.
                        #print 'no'
                        #print 'higher order stabiliser:'
                        #print '%s' % (str(hoStabs[i]))
                        #print 'has no subgroup:'
                        #print '%s' % (str(v.stabiliser))
                        del hoStabs[i]
                index = v.final.order/subGroup.order
                if hoStabs != []:
                    #print 'add True'
                    higherOrderStabiliserProps.append({
                            'class': subGroup, 'index': index, 'filtered': i
                        }
                    )
                    v.hoStabs.append(hoStabs)
                    v.indexCovered[index] = True
                    #print 'subOrbitsLengths, finalSymClass', v.final.__class__
                #else:
                #    print 'filetered out subgroup', subGroup
                #    print 'add False'
            #else:
            #    print 'no'
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
                if not v.stabiliser.isSubgroup(v.hoStabs[n][i]):
                    del v.hoStabs[n][i]
            assert len(v.hoStabs[n]) != 0, (
                "This case should have been checked in __hosp"
            )
            props[n]['filtered'] = 0
        return v.hoStabs[n]

    @property
    def lowerOrderStabiliserProps(v):
        """Get possible sub orbit classes for alternative higher order stabilisers

        TODO
        """
        try:
            assert v.__losPropsCalled == True, 'if this exists it should be true'
        except AttributeError:
            v.__losProps = v.__losp()
            v.__losPropsCalled = True
        return v.__losProps


    def __losp(v):
        """See lowerOrderStabiliserProps"""

        lowerOrderStabiliserProps = []
        v.loStabs                 = []
        if v.stabiliser.mixed == True:
            # alternative way of colouring by using the direct parents.
            # TODO explain more
            assert v.final.mixed
            #print '__losp: final class', v.final.__class__.__name__
            if v.final.generator != {}:
                v.altFinal = v.final.directParent(
                        setup = v.final.directParentSetup
                    )
            else:
                v.altFinal = v.final.directParent(isometries = [
                        isom for isom in v.final if isom.isDirect()
                    ])
            if v.stabiliser.generator != {}:
                v.altStab = v.stabiliser.directParent(setup =
                        v.stabiliser.directParentSetup
                    )
            else:
                v.altStab = v.stabiliser.directParent(isometries = [
                        isom for isom in v.stabiliser if isom.isDirect()
                    ])

            # TODO: fix; don't copy above code...
            for subGroup in v.altFinal.subgroups:
                assert subGroup.order != 0
                if v.altStab.__class__ in subGroup.subgroups:
                    loStabs = v.altFinal.realiseSubgroups(subGroup)
                    for i in range(len(loStabs)-1, -1, -1):
                        if v.altStab.isSubgroup(loStabs[i]):
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
                            # ho, really

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
                if not v.altStab.isSubgroup(v.loStabs[n][i]):
                    del v.loStabs[n][i]
            assert len(v.loStabs[n]) != 0, (
                "This case should have been checked in __losp"
            )
            props[n]['filtered'] = 0
        return v.loStabs[n]
