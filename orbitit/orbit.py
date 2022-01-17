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
    def __new__(self, v):
        assert len(v) == 2
        assert isinstance(v[0], isometry.Set)
        assert isinstance(v[1], isometry.Set)
        self.final = v[0]
        self.stabiliser = v[1]
        return list.__new__(self, v)

    def __repr__(self):
        s = f"[{repr(self.final)}, {repr(self.stabiliser)}]"
        if __name__ != "__main__":
            s += f"{__name__}({s})"
        return s

    def __str__(self):
        s = "{\n"
        s += f"  final = {self.final}\n"
        s += f"  stabiliser = {self.stabiliser}\n"
        s += "}\n"
        if __name__ != "__main__":
            s = f"{__name__}.{s}"
        return s

    @property
    def higherOrderStabiliserProps(self):
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
            assert self.__hospCalled, 'if this exists it should be true'
        except AttributeError:
            self.__hosProps = self.__hosp()
            self.__hospCalled = True
        return self.__hosProps

    def __hosp(self):
        """See higherOrderStabiliserProps"""
        higherOrderStabiliserProps = []
        self.hoStabs = []
        self.indexCovered = {}
        for subGroup in self.final.subgroups:
            assert subGroup.order != 0, f"{subGroup} ({subGroup.__class__.__name__})"
            if self.stabiliser.__class__ in subGroup.subgroups:
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

                hoStabs = self.final.realise_subgroups(subGroup)
                # from end to beginning, because elements will be filtered out:
                for i in range(len(hoStabs)-1, -1, -1):
                    if self.stabiliser.is_subgroup(hoStabs[i]):
                        break
                    else:
                        # remove this from the list, this is part of the work
                        # of filtering the list. This is not done completely
                        # here since it costs time, and the user might not
                        # choose this sub orbit anyway (hence the break above).
                        # But to save time later, remove it already.
                        del hoStabs[i]
                index = self.final.order // subGroup.order
                if hoStabs:
                    higherOrderStabiliserProps.append({'class': subGroup,
                                                       'index': index,
                                                       'filtered': i})
                    self.hoStabs.append(hoStabs)
                    self.indexCovered[index] = True
                # else filter out, since no real subgroup
            # else: this subgroup of G doesn't have the stabiliser as subgroup
        return higherOrderStabiliserProps

    def higherOrderStabiliser(self, n):
        """Get possible sub orbits for higher order stabilisers

        With this a list of higher order stabilisers of one class is obtained.
        n: the list index in higherOrderStabiliserProps representing the class.
        see also higherOrderStabiliserProps.
        """

        # Make sure the list is initialised.
        props = self.higherOrderStabiliserProps

        # filter rest if needed:
        if not props:
            return []
        if props[n]['filtered'] > 0:
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
                if not self.stabiliser.is_subgroup(self.hoStabs[n][i]):
                    del self.hoStabs[n][i]
            assert len(self.hoStabs[n]) != 0, (
                "This case should have been checked in __hosp"
            )
            props[n]['filtered'] = 0
        return self.hoStabs[n]

    @property
    def lowerOrderStabiliserProps(self):
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
            assert self.__lospCalled, 'if this exists it should be true'
        except AttributeError:
            self.__losProps = self.__losp()
            self.__lospCalled = True
        return self.__losProps

    def __losp(self):
        """See lowerOrderStabiliserProps"""

        lowerOrderStabiliserProps = []
        self.loStabs = []
        # if stabiliser has both direct and opposite isometries
        if self.stabiliser.mixed:
            # alternative way of colouring by using the direct parents; i.e.
            # the parent with only direct isometries
            assert self.final.mixed
            if self.final.generator:
                self.altFinal = self.final.direct_parent(
                        setup=self.final.direct_parent_setup)
            else:
                self.altFinal = self.final.direct_parent(
                    isometries=[isom for isom in self.final if isom.is_direct()])
            if self.stabiliser.generator:
                self.altStab = self.stabiliser.direct_parent(
                    setup=self.stabiliser.direct_parent_setup)
            else:
                self.altStab = self.stabiliser.direct_parent(
                    isometries=[
                        isom for isom in self.stabiliser if isom.is_direct()])

            # TODO: fix; don't copy above code from hosp__
            for subGroup in self.altFinal.subgroups:
                assert subGroup.order != 0
                if self.altStab.__class__ in subGroup.subgroups:
                    loStabs = self.altFinal.realise_subgroups(subGroup)
                    for i in range(len(loStabs)-1, -1, -1):
                        if self.altStab.is_subgroup(loStabs[i]):
                            break
                        else:
                            del loStabs[i]
                    index = self.altFinal.order // subGroup.order
                    try:
                        if self.indexCovered[index]:
                            pass
                    except KeyError:
                        if loStabs != []:
                            lowerOrderStabiliserProps.append({
                                    'class': subGroup,
                                    'index': index, 'filtered': i
                                }
                            )
                            self.loStabs.append(loStabs)
                            # don't add to self.indexCovered, it means covered by
                            # __hosp, really

        return lowerOrderStabiliserProps

    def lowerOrderStabiliser(self, n):
        """Get possible sub orbits for higher order stabilisers

        With this a list of higher order stabilisers of one class is obtained.
        n: the list index in lowerOrderStabiliserProps representing the class.
        see also lowerOrderStabiliserProps.
        """

        # Make sure the list is initialised.
        props = self.lowerOrderStabiliserProps

        # filter rest if needed:
        if props[n]['filtered'] > 0:
            for i in range(props[n]['filtered']-1, -1, -1):
                if not self.altStab.is_subgroup(self.loStabs[n][i]):
                    del self.loStabs[n][i]
            assert len(self.loStabs[n]) != 0, (
                "This case should have been checked in __losp"
            )
            props[n]['filtered'] = 0
        return self.loStabs[n]


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
        assert col_choice['index'] == no_of_cols, f"Cannot divide {no_of_cols} colours"
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
            f"colour alternative {col_alt} doesn't exist (max {self.total_no_of_col_alt - 1})"
        col_quotient_set = col_final_sym / col_syms[col_alt]
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
        s += f"# Color alternative based on {self.same_col_isom}\n".format(self.same_col_isom)
        s += f"# Used colour alternative {self.col_alt} (max {self.total_no_of_col_alt - 1})"
        return s

    def to_js(self):
        js = f"var {self.name} = new Object();\n"
        js += f"{self.name}.descr = new Object();\n"
        js += f"{self.name}.descr.Vs = [\n"
        for v in self.baseShape.Vs:
            js += f"  {v},\n"
        js += '];'
        js += f"{self.name}.descr.Fs = {self.baseShape.Fs};"
        eye = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        js += f"{self.name}.descr.transform = {eye};\n"
        js += f"{self.name}.isoms = [\n"
        # note: all isometries are stored in 'direct'
        for q in self.isoms:
            js += str(q.glMatrix())
            js += ','
        js += '];\n'
        for i, col in enumerate(self.col_per_isom):
            js += f"{self.name}.isoms[{i}].col = [{col[0]}, {col[1]}, {col[2]}];\n"

        if self.axis is not None:
            js += f"{self.name}.rot_axis = {self.axis};\n"

        # The angle domain is used for the slide-bar, therefore the precision
        # isn't very important
        if self.angle_domain:
            js += (
                f"{self.name}.angle_domain = "
                f"[{self.angle_domain[0]:.3f}, {self.angle_domain[1]:.3f}];\n"
            )

        return js
