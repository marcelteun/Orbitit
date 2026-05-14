#!/usr/bin/env python
"""A class for handling setting colours for orbit shapes."""
#
# Copyright (C) 2010-2024 Marcel Tunnissen
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
# Old sins:
# pylint: disable=too-many-positional-arguments

import logging

from orbitit import base as orbit_base
from orbitit import colors, geom_3d, geomtypes, isometry


class ColourDivideError(Exception):
    pass


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

        A higher order stabiliser is a subgroup of G that has the stabiliser as a subgroup.
        Practically this is used for colouring of polyhedra. E.g. The polyhedron is defined by one
        face with some symmetry. Then the higher order stabiliser is the symmetry group of the set
        of faces with the same colour. The groups of different coloured faces are mapped onto each
        other by the orbit that is derived from the higher order stabiliser. This orbit is a
        sub-orbit of the original orbit. The norm of this sub-orbit equals to the amount of colours
        used.

        I.e. it is a stabiliser regarding to set of faces with the same colour, and it is called
        "higher order" because it has the same amount or more symmetries. The same amount if each
        face has a unique colour.

        Return:
        A list of dictionaries with properties of higher order stabilisers. Each dictionary holds:
            'class': higher order stabiliser classes is obtained.
            'order': the amount of orbits this subgroup gives rise to. In the example of face
                colours this is the amount of colours that will be used.
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
                    # With not completely here, it there are more, then
                    # higher_order_stabs[-1] is always valid, but higher_order_stabs[:-1] might not
                    del higher_order_stabs[i]
                if higher_order_stabs:
                    order = self.final.order // sub_group.order
                    higher_order_stab_props.append(
                        {
                            'class': sub_group,
                            'order': order,
                            # filtered: always points out to the last element in higher_order_stabs
                            # but if i > 0, then, [0, i) still need to be checked
                            # TODO remove.
                            # Just check whether the length of self.higher_order_stabs > 1
                            'filtered': i,
                        }
                    )
                    self.higher_order_stabs.append(higher_order_stabs)
                    self.index_covered[order] = True
                # else filter out, since no real subgroup
            # else: this subgroup of G doesn't have the stabiliser as subgroup
        return higher_order_stab_props

    def higher_order_stab(self, n):
        """Get possible higher order stabilisers with index 'n'

        With this a list of higher order stabilisers of one class is obtained.
        This needs to be a method, since it is possible that the list at index n still needs to be
        cleaned up. After calling higher_order_stab_props only the last element of that list has
        been verified.

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


class Shape(geom_3d.OrbitShape):  # pylint: disable=too-many-instance-attributes
    """An extension of the geom_3d.OrbitShape.

    The colours a standardised and the descriptive can be rotated.
    """
    orbit_cols = colors.STD_COLORS

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
        self.json_class = Shape

        if cols:
            self.orbit_cols = cols

        assert no_of_cols <= len(self.orbit_cols), 'Not enough colours defined'
        self.orbit = Orbit((final_sym, stab_sym))

        # Old comment related to lower order stabilisers: TODO: investigate this
        # These were higher order stabiliser groups for stab and final only being direct isoms
        # now the fs_orbit might contain isometries that are not part of
        # the colouring isometries. Recreate the shape with isometries that
        # only have these:

        fs_orbit = self.isometries
        self.index = len(fs_orbit)
        self.isoms = fs_orbit
        self.axis = None
        self.angle_domain = None
        self.col_sym = None
        # Save original
        # TODO: why is this needed?
        self._org_base_vs = self.base_vs

        try:
            self.generate_cols(no_of_cols, col_sym, col_alt)
        except ColourDivideError:
            self.generate_cols(1)

    # TODO: use annotated type hint for col_alt >= 0
    def generate_cols(self, no_of_cols, col_sym: str = "", col_alt: int = 0):
        """Generate colour array for this colour alternative

        no_of_cols: specify the number of colours to be used
        col_sym: there might be more than one symmetries available for the amount of colours, is so
            you can specify here the required symmetry name of the set of faces with the same colour
            Make sure to specify a symmetry that does have the required number of orbits.
        col_alt: if there is more than one possibility for a colour symmetry, specify an index here.
        """
        idx = 0
        col_choice = None
        subgroups = self.orbit.higher_order_stab_props
        for idx, col_choice in enumerate(subgroups):
            if col_choice['order'] == no_of_cols:
                if col_sym in ["", col_choice['class'].__name__]:
                    self.col_sym = col_sym
                    break
        else:
            if col_choice is None:
                msg = "No higher order stabilisers found at all!"
            else:
                msg = (
                    f"Cannot divide {no_of_cols} colours with symmetry {col_sym} over "
                    f"{self.orbit.final.__class__.__name__}"
                )
            raise ColourDivideError(msg)

        self.set_col_alt(idx, col_alt)

    def set_col_alt(self, index: int, col_alt: int = 0):
        """Generate colour array for this colour alternative

        index: index in self.orbit.higher_order_stab
        col_alt: if there is more than one possibility for a colour symmetry, specify an index here.
        """
        # Elements with the same colour are mapped onto each other by:
        self.col_choice_index = index
        col_syms = self.orbit.higher_order_stab(index)
        col_choice = self.orbit.higher_order_stab_props[index]

        # generate colour array for this colour alternative
        self.total_no_of_col_alt = len(col_syms)
        if col_alt >= self.total_no_of_col_alt:
            logging.warning(
                f"colour alternative %i doesn't exist (max %i)",
                col_alt,
                self.total_no_of_col_alt - 1,
            )
            col_alt = self.total_no_of_col_alt - 1
        col_quotient_set = self.orbit.final / col_syms[col_alt]
        self.col_per_isom = []
        for isom in self.isoms:
            for i, sub_set in enumerate(col_quotient_set):
                if isom in sub_set:
                    self.col_per_isom.append(self.orbit_cols[i])
                    break
        # update with correct format
        self.col_alt = col_alt
        self.shape_colors = self.col_per_isom.copy()

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
        name = self.name
        sep = "" if self.name[1] == "_" else "_"  # Don't use seperator for A_, B_ variants
        name = f"n{self.index}{sep}{name}"
        js = f"var {name} = new Object();\n"
        js += f"{name}.descr = new Object();\n"
        js += f"{name}.descr.Vs = [\n"
        for v in self.base_vs:
            js += f"  {v},\n"
        js += '];\n'
        js += f"{name}.descr.Fs = {self.base_shape.fs};"
        eye = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        js += f"{name}.descr.transform = {eye};\n"
        js += f"{name}.isoms = [\n"
        # note: all isometries are stored in 'direct'
        for q in self.isoms:
            js += str(q.glMatrix())
            js += ','
        js += '];\n'
        for i, col in enumerate(self.col_per_isom):
            js += f"{name}.isoms[{i}].col = [{col[0]}, {col[1]}, {col[2]}];\n"

        if self.axis is not None:
            js += f"{name}.rot_axis = {self.axis};\n"

        # The angle domain is used for the slide-bar, therefore the precision
        # isn't very important
        if self.angle_domain:
            js += (
                f"{name}.angle_domain = "
                f"[{self.angle_domain[0]:.3f}, {self.angle_domain[-1]:.3f}];\n"
            )

        return js

    def __repr__(self):
        """Representation of the object."""
        return f"{self.__class__.__name__}.from_dict_data({self.repr_dict['data']})"

    def col_syms_for_index(self, i):
        """Return possible colour symmetries for the requested index."""
        return self.orbit.higher_order_stab(i)

    @property
    def orbit_no_of_cols(self):
        """Return the number of colors set in the JSON file."""
        return self.orbit.higher_order_stab_props[self.col_choice_index]["order"]

    @property
    def col_syms(self):
        """Return possible colour symmetries for the current no of cols and symmetry."""
        return self.col_syms_for_index(self.col_choice_index)

    @property
    def same_col_isom(self) -> str:
        """Return symmetry name of the colour in the final symmetry."""
        return self.orbit.higher_order_stab_props[self.col_choice_index]["class"].__name__

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        result = {
            "class": orbit_base.class_to_json[self.json_class],
            "data": {
                "version": 2,
                "name": self.name,
                "base": {
                    "vs": self.base_shape.vs,
                    "fs": self.base_shape.fs,
                },
                "final_sym": self.final_sym.repr_dict,
                "stab_sym": self.stab_sym.repr_dict,
                "cols": getattr(self, "orbit_cols", ""),
                "no_of_cols": self.orbit_no_of_cols,
                "col_alt": self.col_alt,
                "col_sym": self.same_col_isom,
            },
        }
        if self.axis is not None:
            result["data"]["axis"] = self.axis
        if self.angle_domain:
            result["data"]["angle_domain"] = self.angle_domain

        return result

    @classmethod
    def from_dict_data(cls, data):
        if "version" in data:
            if data["cols"] and isinstance(data["cols"][0][0], float):
                data["cols"] = [[int(chn * 255) for chn in d] for d in data["cols"]]
            obj = cls(
                base=data["base"],
                final_sym=isometry.Set.from_json_dict(data["final_sym"]),
                stab_sym=isometry.Set.from_json_dict(data["stab_sym"]),
                name=data["name"],
                cols=data["cols"],
                no_of_cols=data["no_of_cols"],
                col_alt=data["col_alt"],
                col_sym=data["col_sym"],
            )
            if "axis" in data:
                obj.axis = data["axis"]
            if "angle_domain" in data:
                obj.angle_domain = data["angle_domain"]
        else:
            obj = geom_3d.OrbitShape.from_dict_data(data)
        return obj


orbit_base.class_to_json[Shape] = "orbit_shape_v2"
orbit_base.json_to_class["orbit_shape_v2"] = Shape
