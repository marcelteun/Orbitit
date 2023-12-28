#!/usr/bin/env python
"""A class for handling setting colours for orbit shapes."""
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


from orbitit import base as orbit_base
from orbitit import colors, geom_3d, geomtypes, isometry


class Orbit(list):  # pylint: disable=too-many-instance-attributes
    """A class for handling algebraic orbits."""

    def __new__(cls, v):
        assert len(v) == 2
        assert isinstance(v[0], isometry.Set)
        assert isinstance(v[1], isometry.Set)
        return super().__new__(cls, v)

    def __init__(self, v):
        super().__init__(v)
        self.final = v[0]
        self.stabiliser = v[1]
        self.final_sym_alt = None
        self.stab_sym_alt = None
        self.lower_order_stabs = None
        self.__losp_called = False
        self.__losp_cache = None
        self.higher_order_stabs = None
        self.__hosp_called = False
        self.__hosp_cache = None
        self.index_covered = None

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
    def higher_order_stab_props(self):
        """Get possible sub orbit classes for higher order stabilisers

        A higher order stabiliser is a subgroup of G that has the stabiliser as
        a subgroup. Practically this is used for colouring
        of polyhedra. E.g. The polyhedra is defined by one face with some
        symmetry. Then the higher order stabiliser is the set of faces with the
        same colour. The groups of different coloured faces are mapped onto
        each other by the orbit that is derived from the higher order
        stabiliser. This orbit is a sub-orbit of the original orbit. The norm
        of this sub-orbit equals to the amount of colours used.

        Return:
        A list of dictionaries with properties of higher order stabilisers. Each dictionary holds:
            'class': higher order stabiliser classes is obtained.
            'index': the length of the subgroups in the final group, or the
                     norm of the coset.
        """
        if not self.__hosp_called:
            self.__hosp_cache = self.__hosp()
            self.__hosp_called = True
        return self.__hosp_cache

    def __hosp(self):
        """See higher_order_stab_props"""
        higher_order_stab_props = []
        self.higher_order_stabs = []
        self.index_covered = {}
        for sub_group in self.final.subgroups:
            assert sub_group.order != 0, f"{sub_group} ({sub_group.__class__.__name__})"
            if self.stabiliser.__class__ in sub_group.subgroups:
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

                higher_order_stabs = self.final.realise_subgroups(sub_group)
                # from end to beginning, because elements will be filtered out:
                for i in range(len(higher_order_stabs)-1, -1, -1):
                    if self.stabiliser.is_subgroup(higher_order_stabs[i]):
                        break
                    # remove this from the list, this is part of the work
                    # of filtering the list. This is not done completely
                    # here since it costs time, and the user might not
                    # choose this sub orbit anyway (hence the break above).
                    # But to save time later, remove it already.
                    del higher_order_stabs[i]
                index = self.final.order // sub_group.order
                if higher_order_stabs:
                    higher_order_stab_props.append(
                        {
                            'class': sub_group,
                            'index': index,
                            'filtered': i,
                        }
                    )
                    self.higher_order_stabs.append(higher_order_stabs)
                    self.index_covered[index] = True
                # else filter out, since no real subgroup
            # else: this subgroup of G doesn't have the stabiliser as subgroup
        return higher_order_stab_props

    def higher_order_stab(self, n):
        """Get possible sub orbits for higher order stabilisers

        With this a list of higher order stabilisers of one class is obtained.
        n: the list index in higher_order_stab_props representing the class.
        see also higher_order_stab_props.
        """

        # Make sure the list is initialised.
        props = self.higher_order_stab_props

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
                if not self.stabiliser.is_subgroup(self.higher_order_stabs[n][i]):
                    del self.higher_order_stabs[n][i]
            assert len(self.higher_order_stabs[n]) != 0, (
                "This case should have been checked in __hosp"
            )
            props[n]['filtered'] = 0
        return self.higher_order_stabs[n]

    @property
    def lower_order_stab_props(self):
        """Get possible sub orbit classes for lower order stabilisers

        Lower order stabiliser are very similar to higher order stabiliser.
        These are called lower, since they are lower than higher. For groups
        that have both direct and opposite isometries only the direct
        isometries are considered. Then for this only-direct stabiliser and the
        only-direct final group the higher order stabilisers are generated.

        The same list of dictionaries is returned as in higher_order_stab_props
        """
        if not self.__losp_called:
            self.__losp_cache = self.__losp()
            self.__losp_called = True
        return self.__losp_cache

    def __losp(self):
        """See lower_order_stab_props"""

        lower_order_stab_props = []
        self.lower_order_stabs = []
        # if stabiliser has both direct and opposite isometries
        if self.stabiliser.mixed:
            # alternative way of colouring by using the direct parents; i.e.
            # the parent with only direct isometries
            assert self.final.mixed
            if self.final.generator:
                self.final_sym_alt = self.final.direct_parent(setup=self.final.direct_parent_setup)
            else:
                self.final_sym_alt = self.final.direct_parent(
                    isometries=[isom for isom in self.final if isom.is_direct()])
            if self.stabiliser.generator:
                self.stab_sym_alt = self.stabiliser.direct_parent(
                    setup=self.stabiliser.direct_parent_setup)
            else:
                self.stab_sym_alt = self.stabiliser.direct_parent(
                    isometries=[
                        isom for isom in self.stabiliser if isom.is_direct()])

            # TODO: fix; don't copy above code from hosp__
            for sub_group in self.final_sym_alt.subgroups:
                assert sub_group.order != 0
                if self.stab_sym_alt.__class__ in sub_group.subgroups:
                    lower_order_stabs = self.final_sym_alt.realise_subgroups(sub_group)
                    for i in range(len(lower_order_stabs)-1, -1, -1):
                        if self.stab_sym_alt.is_subgroup(lower_order_stabs[i]):
                            break
                        del lower_order_stabs[i]
                    index = self.final_sym_alt.order // sub_group.order
                    try:
                        if self.index_covered[index]:
                            pass
                    except KeyError:
                        if lower_order_stabs != []:
                            lower_order_stab_props.append(
                                {
                                    'class': sub_group,
                                    'index': index,
                                    'filtered': i,
                                }
                            )
                            self.lower_order_stabs.append(lower_order_stabs)
                            # don't add to self.index_covered, it means covered by
                            # __hosp, really

        return lower_order_stab_props

    def lower_order_stab(self, n):
        """Get possible sub orbits for higher order stabilisers

        With this a list of higher order stabilisers of one class is obtained.
        n: the list index in lower_order_stab_props representing the class.
        see also lower_order_stab_props.
        """

        # Make sure the list is initialised.
        props = self.lower_order_stab_props

        # filter rest if needed:
        if props[n]['filtered'] > 0:
            for i in range(props[n]['filtered']-1, -1, -1):
                if not self.stab_sym_alt.is_subgroup(self.lower_order_stabs[n][i]):
                    del self.lower_order_stabs[n][i]
            assert len(self.lower_order_stabs[n]) != 0, (
                "This case should have been checked in __losp"
            )
            props[n]['filtered'] = 0
        return self.lower_order_stabs[n]


class Shape(geom_3d.OrbitShape):  # pylint: disable=too-many-instance-attributes
    """An extension of the geom_3d.OrbitShape.

    The colours a standardised and the descriptive can be rotated.
    """
    cols = colors.STD_COLORS

    # pylint: disable=too-many-arguments, too-many-locals
    def __init__(
            self,
            base,
            final_sym,
            stab_sym,
            name,
            no_of_cols,
            col_alt=0,
            cols=None,
            col_sym='',
        ):
        """
        base: the descriptive. A dictionary with 'vs' and 'fs'
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
        geom_3d.OrbitShape.__init__(
            self,
            base['vs'],
            base['fs'],
            final_sym=final_sym,
            stab_sym=stab_sym,
            name=name,
            quiet=True,
        )

        if cols:
            self.cols = cols

        assert no_of_cols <= len(self.cols), 'Not enough colours defined'
        # Generate cols:
        self.no_of_cols = no_of_cols
        self.col_alt = col_alt
        self.orbit = Orbit((final_sym, stab_sym))
        col_choices = self.orbit.higher_order_stab_props
        alt_start_index = len(col_choices)
        col_choices.extend(self.orbit.lower_order_stab_props)
        fs_orbit = self.isometries
        # find index in col_choices to use
        idx = 0
        col_choice = None
        for idx, col_choice in enumerate(col_choices):
            if col_choice['index'] == no_of_cols:
                if col_sym in ["", col_choice['class'].__name__]:
                    break
        assert col_choice is not None
        assert col_choice['index'] == no_of_cols, f"Cannot divide {no_of_cols} colours"
        # Usefull data:
        # Elements with the same colour are mapped onto eachother by:
        self.same_col_isom = col_choice['class'].__name__
        # find col symmetry properties
        if idx < alt_start_index:
            col_final_sym = self.orbit.final
            col_syms = self.orbit.higher_order_stab(idx)
        else:
            col_final_sym = self.orbit.final_sym_alt
            col_syms = self.orbit.lower_order_stab(idx - alt_start_index)
            # now the fs_orbit might contain isometries that are not part of
            # the colouring isometries. Recreate the shape with isometries that
            # only have these:
            final_sym = self.orbit.final_sym_alt
            stab_sym = self.orbit.stab_sym_alt
            verts = self.base_vs
            faces = self.base_shape.face_props['fs']
            super().__init__(
                verts,
                faces,
                final_sym=final_sym,
                stab_sym=stab_sym,
                name=self.name,
                quiet=True,
            )
            # note: all isometries are stored in 'direct'
            fs_orbit = self.isometries

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
        self.shape_colors = self.col_per_isom.copy()

        # Compound index n means compound of n elements
        self.index = len(fs_orbit)
        self.isoms = fs_orbit
        self.axis = None
        self.angle_domain = None
        # Save original
        self._org_base_vs = self.base_vs

    def transform_base(self, trans):
        """Rotate the position of the descriptive

        trans: a geomtypes.quat object (or matrix) for left multiplying all
               vertices.
        """
        self.base_vs = [trans * v for v in self.base_vs]

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
        """Undo any rotation."""
        self.base_vs = self._org_base_vs

    def to_off(self, precision=geomtypes.FLOAT_OUT_PRECISION, info=False, color_floats=False):
        """Return to off-format representation."""
        s = self.simple_shape.to_off(precision, info, color_floats)
        s += f"# Color alternative based on {self.same_col_isom}\n".format(self.same_col_isom)
        s += f"# Used colour alternative {self.col_alt} (max {self.total_no_of_col_alt - 1})"
        return s

    def to_js(self):
        """Return javascript representation so it can be shown with the showoff library."""
        js = f"var {self.name} = new Object();\n"
        js += f"{self.name}.descr = new Object();\n"
        js += f"{self.name}.descr.vs = [\n"
        for v in self.base_vs:
            js += f"  {v},\n"
        js += '];'
        js += f"{self.name}.descr.fs = {self.base_shape.fs};"
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


orbit_base.class_to_json[Shape] = "orbit_shape"
