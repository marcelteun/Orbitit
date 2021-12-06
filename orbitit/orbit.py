#!/usr/bin/env python
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


from orbitit import Geom3D, geomtypes, isometry, rgb


class Orbit(list):
    def __new__(this, v):
        assert len(v) == 2
        assert isinstance(v[0], isometry.Set)
        assert isinstance(v[1], isometry.Set)
        this.final = v[0]
        this.stabiliser = v[1]
        return list.__new__(this, v)

    def __repr__(v):
        s = '[{}, {}]'.format(repr(v.final), repr(v.stabiliser))
        if __name__ != '__main__':
            s += '{}({})'.format(__name__, s)
        return s

    def __str__(v):
        s = '{\n'
        s += '  final = {}\n'.format(str(v.final))
        s += '  stabiliser = {}\n'.format(str(v.stabiliser))
        s += '}\n'
        if __name__ != '__main__':
            s = '{}.{}'.format(__name__, s)
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
                str(subGroup), subGroup.__class__.__name__)
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
                index = v.final.order // subGroup.order
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
                    index = v.altFinal.order // subGroup.order
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


class Shape(Geom3D.SymmetricShape):
    # standard colours
    cols_blue = [
         rgb.royalBlue,
         rgb.lightSkyBlue,
         rgb.midnightBlue,
         rgb.steelBlue,
         rgb.azure]

    cols_green = [
         rgb.yellowGreen,
         rgb.lightSeaGreen,
         rgb.darkGreen,
         rgb.limeGreen,
         rgb.darkOliveGreen]

    cols_purple = [
         rgb.plum,
         rgb.slateBlue,
         rgb.blueViolet,
         rgb.seashell,
         rgb.lavender]

    cols_yellow = [
         rgb.gold,
         rgb.yellow,
         rgb.lemonChiffon,
         rgb.khaki,
         rgb.lightGoldenrod]

    cols_red = [
         rgb.firebrick,
         rgb.indianRed,
         rgb.red,
         rgb.peachPuff,
         rgb.lightCoral]

    cols_brown_orange = [
         rgb.tan,
         rgb.saddleBrown,
         rgb.peru,
         rgb.orange,
         rgb.darkGoldenrod]

    cols = [  # alternate from above colours
         rgb.royalBlue,      # 0
         rgb.yellowGreen,
         rgb.plum,           # 2
         rgb.gold,
         rgb.firebrick,
         rgb.tan,            # 5

         rgb.lightSkyBlue,
         rgb.lightSeaGreen,  # 7
         rgb.slateBlue,
         rgb.yellow,
         rgb.indianRed,      # 10
         rgb.saddleBrown,

         rgb.midnightBlue,
         rgb.darkGreen,
         rgb.blueViolet,
         rgb.lemonChiffon,
         rgb.red,
         rgb.peru,

         rgb.steelBlue,
         rgb.limeGreen,
         rgb.seashell,
         rgb.khaki,
         rgb.peachPuff,
         rgb.orange,

         rgb.azure,
         rgb.darkOliveGreen,
         rgb.lavender,
         rgb.lightGoldenrod,
         rgb.lightCoral,
         rgb.darkGoldenrod]

    def __init__(self,
                 base,
                 final_sym, stab_sym,
                 name,
                 no_of_cols, col_alt=0, cols=None, col_sym=''):
        """
        base: the descriptive. A dictionary with 'Vs' and 'Fs'
        final_sym: isometry object describing the final symmetry
        stab_sym: isometry object descibing the stabiliser symmetry as subgroup
                  of the final symmetry
        name: string identifier.
        no_of_cols: number of different colours to divide evenly, using the
                    symmetry: all parts with the same colours will have the
                    same symmetry.
        col_alt: there might be more than one unique way of dividing the number
                 of colours. Here you can specify an index.
        cols: in class.cols colours are pre-defined. Here you can overwrite
              these. Thse are supposed to consist of floating RGB values
              between 0 and 1.
        col_sym: it is possible that 'no_of_cols' is obtained based on
                 different classes (the elements with the same colour have
                 different symmetries) if that is the case then you can specify
                 the symmetry (name) that the elements with the same colour
                 should have, e.g. 'C4'.
        """
        Geom3D.SymmetricShape.__init__(self,
                                       base['Vs'],
                                       base['Fs'],
                                       finalSym=final_sym,
                                       stabSym=stab_sym,
                                       name=name,
                                       quiet=True)

        if cols:
            self.cols = cols

        assert no_of_cols <= len(self.cols), 'Not enough colours defined'
        # Generate cols:
        self.no_of_cols = no_of_cols
        self.col_alt = col_alt
        self.orbit = Orbit((final_sym, stab_sym))
        col_choices = self.orbit.higherOrderStabiliserProps
        alt_start_index = len(col_choices)
        col_choices.extend(self.orbit.lowerOrderStabiliserProps)
        # note: all isometries are stored in 'direct'
        fs_orbit = self.getIsometries()['direct']
        # find index in col_choices to use
        for idx, col_choice in enumerate(col_choices):
            if col_choice['index'] == no_of_cols:
                if col_sym == '' or col_sym == col_choice['class'].__name__:
                    break
        assert col_choice['index'] == no_of_cols,\
            'Cannot divide {} colours'.format(no_of_cols)
        # Usefull data:
        # Elements with the same colour are mapped onto eachother by:
        self.same_col_isom = col_choice['class'].__name__
        # find col symmetry properties
        if idx < alt_start_index:
            col_final_sym = self.orbit.final
            col_syms = self.orbit.higherOrderStabiliser(idx)
        else:
            col_final_sym = self.orbit.altFinal
            col_syms = self.orbit.lowerOrderStabiliser(idx - alt_start_index)
            # now the fs_orbit might contain isometries that are not part of
            # the colouring isometries. Recreate the shape with isometries that
            # only have these:
            final_sym = self.orbit.altFinal
            stab_sym = self.orbit.altStab
            verts = self.getBaseVertexProperties()['Vs']
            faces = self.getBaseFaceProperties()['Fs']
            Geom3D.SymmetricShape.__init__(self, verts, faces,
                                           finalSym=final_sym,
                                           stabSym=stab_sym,
                                           name=self.name,
                                           quiet=True)
            # note: all isometries are stored in 'direct'
            fs_orbit = self.getIsometries()['direct']

        # generate colour array for this colour alternative
        self.total_no_of_col_alt = len(col_syms)
        assert col_alt < self.total_no_of_col_alt,\
            "colour alternative {} doesn't exist (max {})".format(
                col_alt, self.total_no_of_col_alt - 1)
        col_quotient_set = col_final_sym  //  col_syms[col_alt]
        self.col_per_isom = []
        for isom in fs_orbit:
            for i, sub_set in enumerate(col_quotient_set):
                if isom in sub_set:
                    self.col_per_isom.append(self.cols[i])
                    break
        # update with correct format
        self.setFaceColors([([col], []) for col in self.col_per_isom])

        # Compound index n means compound of n elements
        self.index = len(fs_orbit)
        self.isoms = fs_orbit
        self.axis = None
        self.angle_domain = None
        # Save original
        self.baseShape.org_Vs = self.baseShape.Vs

    def transform_base(self, trans):
        """Rotate the position of the descriptive

        trans: a geomtypes.quat object (or matrix) for left multiplying all
               vertices.
        """
        self.setVs([trans * v for v in self.baseShape.Vs])

    def set_rot_axis(self, axis, domain=None):
        """Set the rotation axis for rotating the descriptive.

        axis: a geomtypes.Vec3 object around which the descriptive will be
              rotated.
        """
        self.axis = axis
        self.angle_domain = domain

    def rot_base(self, rad):
        """Rotate the descriptive 'rad' radians around the current axis.

        Before calling this set_rot_axis should have been called.
        rad: an angle in radians
        """
        self.transform_base(geomtypes.Rot3(axis=self.axis, angle=rad))

    def reset_rotation(self):
        self.setVs(self.baseShape.org_Vs)

    def to_off(self):
        s = self.simple_shape.toOffStr(color_floats=True)
        s += "# Color alternative based on {}\n".format(self.same_col_isom)
        s += "# Used colour alternative {} (max {})".format(
                self.col_alt, self.total_no_of_col_alt - 1)
        return s

    def to_js(self):
        js = 'var {} = new Object();\n'.format(self.name)
        js += '{}.descr = new Object();\n'.format(self.name)
        js += '{}.descr.Vs = [\n'.format(self.name)
        for v in self.baseShape.Vs:
            js += '  {},\n'.format(v)
        js += '];'
        js += '{}.descr.Fs = {};'.format(self.name, self.baseShape.Fs)
        eye = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        js += '{}.descr.transform = {};\n'.format(self.name, eye)
        js += '{}.isoms = [\n'.format(self.name)
        # note: all isometries are stored in 'direct'
        for q in self.isoms:
            js += str(q.glMatrix())
            js += ','
        js += '];\n'
        for i, col in enumerate(self.col_per_isom):
            js += '{}.isoms[{}].col = [{}, {}, {}];\n'.format(
                self.name, i, col[0], col[1], col[2])

        if self.axis is not None:
            js += '{}.rot_axis = {};\n'.format(self.name, self.axis)

        # The angle domain is used for the slide-bar, therefore the precision
        # isn't very important
        if self.angle_domain:
            js += '{}.angle_domain = [{:.3f}, {:.3f}];\n'.format(
                self.name, self.angle_domain[0], self.angle_domain[1])

        return js
