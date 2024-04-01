#!/usr/bin/env python
"""
Geometry types specifically related to 3D
"""
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
# ------------------------------------------------------------------
# Old sins:
# pylint: disable=too-many-lines,too-many-return-statements,
# pylint: disable=too-many-locals,too-many-statements,too-many-ancestors
# pylint: disable=too-many-instance-attributes,too-many-arguments
# pylint: disable=too-many-branches,too-many-nested-blocks
# pylint: disable=too-few-public-methods,too-many-public-methods


from abc import ABC
import copy
import logging
import math
from functools import reduce
import wx

from OpenGL import GL

from orbitit import base, geom_2d, geomtypes, glue, indent, isometry, PS, rgb, Scenes3D

# TODO:
# - Test the gl stuf of SimpleShape: create an Interactive3DCanvas
#   the Symmetry stuff should not contain any shape stuff
# - Add a flatten option to the Symmetric Face: resulting will be a SimpleShape
#   that can be exported.
# - Add class function: intersect faces: which will return a new shape for
#   which the faces do not intersect anymore. Then there should be a class
#   function for converting the faces to PS string as is.
# - remove depedency towards cgkit: move to Scientific Python: make your own
#   wrapper to abstract from this dependency?
# - Add possible scene objects, containing shapes.
# - add transforms
# - add print pieces (cp from p3D)
# - function to_postscript finds intersection: this should be part of a separate
#   functons mapping the SimpleShape on a shape consisting of none intersecting
#   pieces. This could be a child of SimpleShape.
# - add function to filter out vertices that ly within a certain area: these
#   should be projected on the avg of all of them: use a counter for this.
# - clean up a bit: some functions return objects, other return the strings.

# Done
# - edges after reading off file


def vec(x, y, z):
    """Return 3D vector type."""
    return geomtypes.Vec3([x, y, z])


def gl_vertex_pointer(v):
    """Wrapper of GL.glVertexPointerf to disable pylint no-member issue."""
    return GL.glVertexPointerf(v)  # pylint: disable=no-member


def gl_normal_pointer(v):
    """Wrapper of GL.glNormalPointerf to disable pylint no-member issue."""
    return GL.glNormalPointerf(v)  # pylint: disable=no-member


def gl_draw_elements(s, e):
    """Wrapper of GL.glDrawElementsui to disable pylint no-member issue."""
    return GL.glDrawElementsui(s, e)  # pylint: disable=no-member


E = geomtypes.E  # Identity
I = geomtypes.I  # Central inversion

# constant that have deal with angles
RAD2DEG = 180.0 / math.pi
DEG2RAD = math.pi / 180
R1_2 = math.pi  # 1/2 of a circle

R1_3 = 2 * math.pi / 3  # 1/3 of a circle
R2_3 = 2 * R1_3  # 2/3 of a circle

R1_4 = math.pi / 2  # 1/4 of a circle
R3_4 = 3 * R1_4  # 3/4 of a circle

R1_5 = 2 * math.pi / 5  # 1/5 of a circle
R2_5 = 2 * R1_5  # 2/5 of a circle
R3_5 = 3 * R1_5  # 3/5 of a circle
R4_5 = 4 * R1_5  # 4/5 of a circle

V2 = math.sqrt(2)
V3 = math.sqrt(3)
V5 = math.sqrt(5)

TAU = (V5 + 1) / 2

# rotation needed from standard isometries.A4 where the z-axis is shared with a 2-fold axis to a
# position where the z-axis is shared with a 3-fold axis.
A4_Z_O2_TO_O3 = geomtypes.Rot3(angle=math.atan(V2), axis=geomtypes.Vec3([1, 1, 0]))
A4_Z_O2_TO_O3 = (
    geomtypes.Rot3(angle=math.pi / 4, axis=geomtypes.Vec3([0, 0, 1])) * A4_Z_O2_TO_O3
)

S4_Z_O4_TO_O3 = A4_Z_O2_TO_O3
S4_Z_O4_TO_O2 = geomtypes.Rot3(angle=math.pi / 4, axis=geomtypes.Vec3([0, 1, 0]))

# rotation needed from standard isometries.A5 where the z-axis is shared with a 2-fold axis to a
# position where the z-axis is shared with a 5-fold axis
A5_Z_O2_TO_O5 = geomtypes.Rot3(angle=math.atan(TAU), axis=geomtypes.Vec3([1, 0, 0]))

# rotation needed from standard isometries.A5 where the z-axis is shared with a 2-fold axis to a
# position where the z-axis is shared with a 3-fold axis
A5_Z_O2_TO_O3 = geomtypes.Rot3(angle=math.atan(2 - TAU), axis=geomtypes.Vec3([1, 0, 0]))


def is_int(int_str):
    """Return whether the string represents an integer."""
    try:
        _ = int(int_str)
        return True
    except ValueError:
        return False


def read_off_file(fd, regen_edges=True, name=""):
    """Reads an the std 'off' format of a 3D object and returns an object of the
    SimpleShape class.

    fd: the file descriptor of a file that is opened with read permissions.
    regen_edges: if set to True then the shape will recreate the edges for all faces, i.e. all faces
        will be surrounded by edges. Edges will be filtered so that shared edges between faces, i.e.
        edges that have the same vertex index, only appear once. The creation of edges is not
        optimised and can take a long time.
    return: an object of the SimpleShape class.
    """
    states = {"checkOff": 0, "readSizes": 1, "readVs": 2, "readFs": 3, "readOk": 4}
    no_of_vs = 0
    no_of_fs = 0
    no_of_es = 0
    # Initialise all for pylint, though state machine will take care of most
    vs = []
    es = []
    fs = []
    cols = []
    face_cols = []
    i = 0
    # A dictionary where the key and value pairs are exchanged, for debugging
    # purposes:
    states_to_name = {value: key for key, value in states.items()}
    state = states["checkOff"]
    vertex_radius = 0
    edge_radius = 0
    for line in fd:
        words = line.split()
        if len(words) > 0 and words[0][0] != "#":
            if state == states["checkOff"]:
                if words[0] == "OFF":
                    state = states["readSizes"]
                else:
                    break
                logging.debug("OFF file format recognised")
            elif state == states["readSizes"]:
                # the function assumes: no comments in beween the 3 nrs
                assert words[0].isdigit()
                assert words[1].isdigit()
                assert words[2].isdigit()
                no_of_vs = int(words[0])
                no_of_fs = int(words[1])
                no_of_es = int(words[2])
                # Dont check Euler: in a compound for each part F + V - E = 2
                # So the difference 2 becomes 2n for a compound of n.
                # assert no_of_es + 2 == no_of_fs + no_of_vs
                state = states["readVs"]
                vs = []
                logging.debug(
                    "will read %d vertices, %d faces and %d edges",
                    no_of_vs,
                    no_of_fs,
                    no_of_es,
                )
            elif state == states["readVs"]:
                # the function assumes: no comments in beween (x, y, z) of vs
                vs.append(geomtypes.Vec3(words[0:3]))
                logging.debug("V[%d] = %s", i, vs[-1])
                i = i + 1
                if i == no_of_vs:
                    state = states["readFs"]
                    fs = []
                    cols = []
                    face_cols = list(range(no_of_fs))
                    i = 0
                    if no_of_fs == 0:
                        state = states["readOk"]
                        logging.info("Note: the OFF file only contains vertices")
                        vertex_radius = 0.05
            elif state == states["readFs"]:
                # the function assumes: no comments in beween "q i0 .. iq-1 r g b"
                assert words[0].isdigit(), f"error interpreting line as face {words}"
                len_f = int(words[0])
                if len_f > 0:
                    assert len(words) >= len_f + 4 or len(words) == len_f + 1
                    face = [int(words[j]) for j in range(1, len_f + 1)]
                    if len_f >= 3:
                        fs.append(face)
                        if len(words) == len_f + 1:
                            cols.append([0.8, 0.8, 0.8])
                        else:
                            if is_int(words[len_f + 1]):
                                cols.append(
                                    [int(words[j]) for j in range(len_f + 1, len_f + 4)]
                                )
                            else:
                                cols.append(
                                    [
                                        int(255 * float(words[j]))
                                        for j in range(len_f + 1, len_f + 4)
                                    ]
                                )
                        logging.debug("face[%d] = %s", i, fs[-1])
                        logging.debug("col[%d] = %s", i, cols[-1])
                    else:
                        if len_f == 2:
                            # this is an edge really...
                            es.extend(face)
                            edge_radius = 0.15
                            logging.debug("face[%d] = %s is an edge", i, face)
                            # what about different edge colours?
                        else:
                            # since vertices are defined explicitely, show them
                            vertex_radius = 0.05
                            logging.info(
                                "ignoring face %d with only %d vertices", i, len_f
                            )
                    i = i + 1
                    if i == no_of_fs:
                        state = states["readOk"]
                        break
            else:
                break
    assert state == states["readOk"], (
        f"EOF occurred while not done reading:\n"
        f"\tWould read {no_of_vs} vertices and {no_of_fs} faces;\n"
        f"\tcurrent state {states_to_name[state]} with {i} items read"
    )
    shape = SimpleShape(vs, fs, es, colors=(cols, face_cols))
    # Note that Orbitit's panel.setShape will ignore these anyway...
    if vertex_radius != 0:
        shape.vertex_props = {"radius": vertex_radius}
    if edge_radius != 0:
        shape.edge_props = {"radius": edge_radius}
    if name != "":
        shape.name = name
    # If the file defines edges (faces of length 2) then don't recreate any
    # edges, even if requested
    if regen_edges and len(es) == 0:
        shape.regen_edges()
    return shape


def save_file(fd, shape):
    """
    Save a shape in a file descriptor

    The caller still need to close the filde descriptor afterwards
    """
    fd.write("import orbitit\n")
    fd.write(f"shape = {repr(shape)}")


class Fields:
    """
    This class is an empty class to be able to set some fields, like structures
    in C.
    """


class Line3D(geomtypes.Line):
    """Model a line in 3D

    This can either be infinite lines or line segments.
    """

    str_precision = 2

    def __init__(self, p0, p1=None, v=None, is_segment=False):
        """
        Define a line in 3D space.

        Either specify two distinctive points p0 and p1 on the line or specify
        a base point p0 and directional vector v. Points p0 and p1 should have
        a length of 3 and may be a geom_types.Vec3 type.
        """
        # make sure to have vector types internally
        p0 = geomtypes.Vec3(p0)
        if p1 is None:
            assert v is not None
            v = geomtypes.Vec3(v)
            geomtypes.Line.__init__(self, p0, v=v, d=3, is_segment=is_segment)
        else:
            assert v is None
            p1 = geomtypes.Vec3(p1)
            geomtypes.Line.__init__(self, p0, p1, d=3, is_segment=is_segment)

    # redefine to get vec3 types:
    def _set_points(self, p0, p1):
        """From two points p0 and p1 define the line."""
        self._define_line(p0, p1 - p0)

    def get_point(self, t):
        """Return the point on the line that equals to self.b + t*self.v (or [] when t is None)"""
        if t is not None:
            return self.p + t * self.v
        return []

    def squared_distance_to(self, point):
        """Return the square distance to a point."""
        # see p81 of E.Lengyel
        q = geomtypes.Vec3(point)
        hyp = q - self.point
        prj_q = hyp * self.v
        return (hyp * hyp) - ((prj_q * prj_q) / (self.v * self.v))

    def discriminant_with_line(self, line):
        """Return the discriminant between two lines as according to p82 of E.Lengyel."""
        dot = self.v * line.v
        return (self.v * self.v) * (line.v * line.v) - dot * dot

    def is_parallel_with(self, line):
        """Return whether the current line is parallel with the specified line."""
        # p82 of E.Lengyel
        return self.discriminant_with_line(line) == 0

    def __str__(self):
        return f"(x, y, z) = {self.p} + t * {self.v}"


class Triangle:
    """Model a triangle in 3D space."""

    def __init__(self, v0, v1, v2):
        self.v = [
            vec(v0[0], v0[1], v0[2]),
            vec(v1[0], v1[1], v1[2]),
            vec(v2[0], v2[1], v2[2]),
        ]
        self._normal = vec(0, 0, 0)

    # since there is an extra parameter this isn't a property
    def normal(self, normalise=False):
        """Return the normal of the triangle."""
        if self._normal.norm() == 0:
            self._normal = (self.v[1] - self.v[0]).cross(self.v[2] - self.v[0])
            if normalise:
                try:
                    self._normal = self._normal.normalize()
                except ZeroDivisionError:
                    pass
        return self._normal


class PlaneFromNormal:
    """Create a plane from a normal and one known point

    The plane class will contain the fields 'normal' expressing the normalised norm
    and a 'D' such that for a point P in the plane 'D' = -normal.P, i.e.
    normal_x x + normal_y y + normal_z z + D = 0 is the equation of the plane.
    """

    def __init__(self, normal, point):
        self.normal = normal
        self.D = geomtypes.RoundedFloat(-self.normal * geomtypes.Vec3(point))

    def intersect_with_plane(self, plane):
        """Calculates the intersections of 2 planes.

        If the planes are parallel None is returned (even if the planes define
        the same plane) otherwise a line is returned.
        """
        if plane is None:
            return None
        n0 = self.normal
        n1 = plane.normal
        if n0 in (n1, -n1):
            return None
        v = n0.cross(n1)
        # v = v.normalise()
        # for to_postscript self.normal == [0, 0, 1]; handle more efficiently.
        if n0 == geomtypes.Vec([0, 0, 1]):
            # simplified situation from below:
            z = -self.D
            mat = geomtypes.Mat([geomtypes.Vec(n1[0:2]), geomtypes.Vec(v[0:2])])
            q = mat.solve(geomtypes.Vec([-plane.D - n1[2] * z, -v[2] * z]))
            q = geomtypes.Vec([q[0], q[1], z])
        else:
            # See bottom of page 86 of Maths for 3D Game Programming.
            mat = geomtypes.Mat([n0, n1, v])
            q = mat.solve(geomtypes.Vec([-self.D, -plane.D, 0]))
        return Line3D(q, v=v)

    def __eq__(self, plane):
        """Return True if the planes define the same one."""
        return (self.normal == plane.normal and self.D == plane.D) or (
            self.normal == -plane.normal and self.D == -plane.D
        )

    def __repr__(self):
        return "{} x + {} y + {} z + {} = 0".format(  # pylint: disable=consider-using-f-string
            geomtypes.RoundedFloat(self.normal[0]),
            geomtypes.RoundedFloat(self.normal[1]),
            geomtypes.RoundedFloat(self.normal[2]),
            self.D,
        )


class Plane(PlaneFromNormal):
    """Create a plane from 3 points in the plane.

    The points should be unique.
    """

    def __init__(self, p0, p1, p2):
        assert not p0 == p1, f"\n  p0 = {p0},\n  p1 = {p1}"
        assert not p0 == p2, f"\n  p0 = {p0},\n  p2 = {p2}"
        assert not p1 == p2, f"\n  p1 = {p1},\n  p2 = {p2}"
        super().__init__(self._norm(p0, p1, p2), p0)

    @staticmethod
    def _norm(p0, p1, p2):
        """calculate the normalised plane normal"""
        v1 = geomtypes.Vec3(p0) - geomtypes.Vec3(p1)
        v2 = geomtypes.Vec3(p0) - geomtypes.Vec3(p2)
        cross = v1.cross(v2)
        if geomtypes.FloatHandler.eq(cross.norm(), 0):
            raise ValueError("Points are on one line")
        result = v1.cross(v2).normalize()
        return result


TRI_CW = 1  # clockwise triangle vertices to get outer normal
TRI_CCW = 2  # counter-clockwise triangle vertices to get outer normal
TRI_OUT = 3  # the normal pointing away from the origin is the normal
TRI_IN = 4  # the normal pointing towards from the origin is the normal


class SimpleShape(base.Orbitit):
    """
    This class decribes a simple 3D object consisting of faces and edges.

    Attributes:
    shape_colors: same as the colors parameter in __init__, see that method.
    """

    normal_direction = TRI_OUT

    def __init__(
        self,
        vs,
        fs,
        es=None,
        ns=None,
        colors=None,
        name="SimpleShape",
        orientation=None,
    ):
        """
        vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by gl_draw
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each face with
                   index 'i' in fs which colour index from the parameter color
                   is used for this face.  If empty then colors[0][0] shall be
                   used for each face.
                Note the object may update these.
        name: A string expressing the name. This name is used e.g. when
            exporting to other formats, like PS.
        orientation: orientation of the base shape. This is an isometry operation.
        """
        if not es:
            es = []
        if not ns:
            ns = []
        self.fs = []
        self.vs = []
        self.es = []
        self.dimension = 3
        self.face_normals = []
        self.generate_normals = True
        self._shape_colors = [[], []]
        self.name = name
        # For four below, see create_vertex_normals
        self.normal_per_vertex = []
        self.vertex_per_normal = []
        self.triangulated_faces_n_index = []
        self.edges_n_index = []
        self.face_normals_up_to_date = False
        self.face_normals_normalised = None
        self.gl_initialised = False
        self.gl = Fields()
        self.gl.sphere = None
        self.gl.vertex_radius = -1
        self.gl.vertex_col = [255, 255, 200]
        self.gl.update_vertices = True
        self.gl.sphere_vertices = False
        self.gl.edge_radius = -1
        self.gl.edge_col = [25, 25, 25]
        self.gl.cylindrical_edges = False
        self.gl.cyl = None
        self.gl.draw_faces = True
        self.gl.force_set_vs = False
        self.saved_ns = None
        self.saved_vs = None
        self.spheres_radii = Fields()
        self.spheres_radii.precision = 12
        self.spheres_radii.circumscribed = 0
        self.spheres_radii.mid = 0
        self.spheres_radii.inscribed = 0
        self.len_to_edge = {}
        self.fs_gravity = []
        self.equal_colored_fs = []
        self.no_of_fs = 0
        # This is save so heirs can still use repr_dict from this class
        self.json_class = SimpleShape
        self.gl.force_set_vs = (
            False  # set to true if a scene contains more than 1 shape
        )
        if not colors or not colors[0]:
            colors = ([rgb.gray95[:]], [])
        self.zoom_factor = 1.0
        self.vertex_props = {"vs": vs, "ns": ns, "radius": -1.0}
        self.edge_props = {"es": es, "draw_edges": True}
        self.face_props = {"fs": fs, "colors": colors}
        if orientation:
            self.orientation = orientation
            if not orientation.is_opposite():
                self.normal_direction = TRI_IN
        else:
            self.orientation = geomtypes.E

    def __repr__(self):
        # s = indent.Str('%s(\n' % base.find_module_class_name(self.__class__, __name__))
        s = indent.Str("SimpleShape(\n")
        s = s.add_incr_line("vs=[")
        s.incr()
        try:
            s = s.glue_line(
                ",\n".join(indent.Str(repr(v)).reindent(s.indent) for v in self.vs)
            )
        except AttributeError:
            logging.error("Are you sure the vertices are all of type geomtypes.Vec3?")
            raise
        s = s.add_decr_line("],")
        s = s.add_line("fs=[")
        s.incr()
        s = s.glue_line(
            ",\n".join(indent.Str(repr(f)).reindent(s.indent) for f in self.fs)
        )
        s = s.add_decr_line("],")
        s = s.add_line(f"es={self.es},")
        s = s.add_line(f"colors={self._shape_colors},")
        s = s.add_line(f'name="{self.name}"')
        s = s.add_decr_line(")")
        if __name__ != "__main__":
            s = s.insert(f"{__name__}.")
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object.

        Only essential parts are saved. E.g. orientation isn't essential here.
        """
        return {
            "class": base.class_to_json[self.json_class],
            "data": {
                "name": self.name,
                "vs": self.vs,
                "fs": self.fs,
                "cols": self._shape_colors[0],
                "face_cols": self._shape_colors[1],
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        """Create object from a dictionary created by repr_dict."""
        # older version used a float between 0 and 1
        if isinstance(data["cols"][0][0], float):
            data["cols"] = [[int(chn * 255) for chn in d] for d in data["cols"]]
        return cls(
            [geomtypes.Vec3(v) for v in data["vs"]],
            data["fs"],
            colors=(data["cols"], data["face_cols"]),
            name=data["name"],
        )

    def save_file(self, fd):
        """
        Save a shape in a file descriptor

        The caller still need to close the filde descriptor afterwards
        """
        save_file(fd, self)

    @property
    def simple_shape(self):
        """To be compatible: derivatives of this class will have this property

        Some classes that inherit from this class need to implement self.
        Implement here to be compatible.
        """
        return self

    def filter_faces(self, keep_one=True):
        """Remove faces using the same vertices (independent of their colour)

        keep_one: of the faces with duplicates keep at least one.
        """
        v_props = self.vertex_props
        f_props = self.face_props
        fs = f_props["fs"]
        org_cols = f_props["colors"]
        d = {}
        for i, face in enumerate(fs):
            face_cp = face[:]
            face_cp.sort()
            try:
                d[tuple(face_cp)].append(i)
            except KeyError:
                d[tuple(face_cp)] = [i]

        new_fs = []
        col_idx = []
        if keep_one:
            for i in d.values():
                new_fs.append(fs[i[0]])
                col_idx.append(org_cols[1][i[0]])
        else:
            for i in d.values():
                if len(i) == 1:
                    new_fs.append(fs[i[0]])
                    col_idx.append(org_cols[1][i[0]])
        new_cols = (copy.deepcopy(org_cols[0]), col_idx)
        shape = SimpleShape([], [], [])
        shape.vertex_props = v_props
        f_props["fs"] = new_fs
        f_props["colors"] = new_cols
        shape.face_props = f_props
        return shape

    def clean_shape(self, precision):
        """Return a new shape for which vertices are merged and degenerated faces are deleted.

        The shape will not have any edges.

        precision: number of decimals to consider when deciding whether two floating point numbers
            are equal.
        """
        v_props = self.vertex_props
        f_props = self.face_props
        vs_copied = copy.deepcopy(v_props["vs"])
        fs_copied = copy.deepcopy(f_props["fs"])
        with geomtypes.FloatHandler(precision):
            glue.mergeVs(vs_copied, fs_copied, precision)
        # this may result on less faces, which breaks the colours!
        # TODO either update the colors immediately or return an array with
        # deleted face indices.
        glue.clean_up_vs_fs(vs_copied, fs_copied)
        v_props["vs"] = vs_copied
        f_props["fs"] = fs_copied
        shape = SimpleShape([], [], [])
        shape.vertex_props = v_props
        shape.face_props = f_props
        return shape

    @property
    def vertex_props(self):
        """
        Return the current vertex properties

        Returned is a dictionary with the keywords vs, radius, color and ns.
        vs: an array of vertices.
        radius: If > 0.0 draw vertices as spheres with the specified colour. If
                no spheres are required (for preformance reasons) set the radius
                to a value <= 0.0.
        color: optional array with 3 rgb values between 0 and 255.
        ns: an array of normals (per vertex) This value might be None if the
            value is not set. If the value is set it is used by gl_draw
        """
        return {
            "vs": self.vs,
            "radius": self.gl.vertex_radius,
            "color": self.gl.vertex_col,
            "ns": self.ns,
        }

    @vertex_props.setter
    def vertex_props(self, props):
        """
        Set the vertices and how/whether vertices are drawn in OpenGL.

        Accepted are the optional (keys) parameters:
        - vs,
        - radius,
        - color.
        - ns.
        See getter for the explanation of the keys.
        """
        if props:
            if "vs" in props and props["vs"] is not None:
                self.vs = [geomtypes.Vec3(v) for v in props["vs"]]
                self.vertex_range = range(len(self.vs))
                self.gl.update_vertices = True
                self.face_normals_up_to_date = False
            if "ns" in props and props["ns"] is not None:
                self.ns = props["ns"]
            if "radius" in props and props["radius"] is not None:
                self.gl.vertex_radius = props["radius"]
                self.gl.sphere_vertices = props["radius"] > 0.0
                if self.gl.sphere_vertices:
                    if self.gl.sphere is not None:
                        del self.gl.sphere
                    self.gl.sphere = Scenes3D.VSphere(radius=props["radius"])
            if "color" in props and props["color"] is not None:
                if props["color"]:
                    assert isinstance(
                        props["color"][0], int
                    ), "Oops: old float format, use int up to 255 now"
                self.gl.vertex_col = props["color"]

    def gl_force_set_vs(self, do):
        """
        Force to set the vertices in OpenGL, independently on the updated vertices flag.

        Normally the vertices in OpenGL are only reprogrammed if the vertices were updated, but
        setting this flag will always reprogram the vertices.
        """
        self.gl.force_set_vs = do

    @property
    def edge_props(self):
        """
        Return the current edge properties

        Returned is a dictionary with the keywords es, radius, color, draw_edges
        es: a qD array of edges, where i and j in edge [ .., i, j,.. ] are
            indices in vs.
        radius: If > 0.0 draw vertices as cylinders with the specified colour.
                If no cylinders are required (for preformance reasons) set the
                radius to a value <= 0.0 and the edges will be drawn as lines,
                using glPolygonOffset.
        color: array with 3 rgb values between 0 and 1.
        draw_edges: settings that expresses whether the edges should be drawn at all.
        """
        return {
            "es": self.es,
            "radius": self.gl.edge_radius,
            "color": self.gl.edge_col,
            "draw_edges": self.gl.draw_edges,
        }

    @edge_props.setter
    def edge_props(self, props):
        """
        Specify the edges and set how they are drawn in OpenGL.

        Accepted is a dictionary with the following optional keys:
          - es,
          - radius,
          - color,
          - draw_edges.
        """
        if props:
            if "es" in props and props["es"] is not None:
                self.es = props["es"]
            if "radius" in props and props["radius"] is not None:
                self.gl.edge_radius = props["radius"]
                self.gl.cylindrical_edges = props["radius"] > 0.0
                if self.gl.cylindrical_edges:
                    if self.gl.cyl is not None:
                        del self.gl.cyl
                    self.gl.cyl = Scenes3D.P2PCylinder(radius=props["radius"])
            if "color" in props and props["color"] is not None:
                if props["color"]:
                    assert isinstance(
                        props["color"][0], int
                    ), "Oops: old float format, use int up to 255 now"
                self.gl.edge_col = props["color"]
            if "draw_edges" in props and props["draw_edges"] is not None:
                self.gl.draw_edges = props["draw_edges"]

    def regen_edges(self):
        """
        Recreates the edges in the 3D object by using an adges for every side of
        a face, i.e. all faces will be surrounded by edges.

        Edges will be filtered so that shared edges between faces,
        i.e. edges that have the same vertex index, only appear once.
        The creation of edges is not optimised and can take a long time.
        """
        added_edges = []
        es = []

        def add_edge(i, j):
            if i < j:
                edge = [i, j]
            elif i > j:
                edge = [j, i]
            else:
                return
            if not edge in added_edges:
                added_edges.append(edge)
                es.extend(edge)

        for face in self.fs:
            last_idx = len(face) - 1
            for i in range(last_idx):
                add_edge(face[i], face[i + 1])
            # handle the edge from the last vertex to the first vertex separately
            # (instead of using % for every index)
            add_edge(face[last_idx], face[0])
        self.es = es

    @property
    def face_props(self):
        """
        Return the current face properties.

        Returned is a dictionary with the keywords fs, colors, and draw_faces.
        fs: Optional array of faces, that do not need to be triangular. It is a
            hierarchical array, ie it consists of sub-array, where each
            sub-array describes one face. Each n-sided face is desribed by n
            indices. Empty on default. Using triangular faces only gives a
            better performance.
            If fs is None, then the previous specified value will be used.
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each face with
                   index 'i' in fs which colour index from the parameter color
                   is used for this face. If empty then colors[0][0] shall be
                   used for each face.
                   It should have the same length as fs (or the current faces if
                   fs not specified) otherwise the parameter is ignored and the
                   face colors are set by some default algorithm.
        draw_faces: settings that expresses whether the faces should be drawn.
        """
        return {
            "fs": self.fs,
            "colors": self._shape_colors,
            "draw_faces": self.draw_faces,
        }

    @face_props.setter
    def face_props(self, props):
        """
        Define the properties of the faces.

        Send in an dictionary with the following keys:
          - fs,
          - colors,
          - draw_faces.
        See getter for the explanation of the keys.
        """
        if props:
            if "fs" in props and props["fs"] is not None:
                self._set_faces(props["fs"])
            if "colors" in props and props["colors"] is not None:
                self.shape_colors = props["colors"]
            self._divide_col()
            if "draw_faces" in props and props["draw_faces"] is not None:
                self.draw_faces = props["draw_faces"]

    @staticmethod
    def triangulate(faces):
        """Divide faces into triangles

        The faces aren't triangulated so that the triangles cover the same area. This is mainly done
        to use the stencil buffer for concave polygons.

        return: a new list with faces, but each face is replaced with one list with vertex indices,
        which would form triangles if they are grouped by three.
        """
        return [
            # i+1 before i, to keep clock-wise direction
            [t for i in range(1, len(f) - 1) for t in (f[0], f[i + 1], f[i])]
            for f in faces
        ]

    def faces_updated(self):
        """Call this method when faces were updated without setting face_props

        E.g. when reverse_face is used or any other time the faces array is updated.
        """
        self.triangulated_faces_n_index = self.triangulate(self.fs)
        self.no_of_fs = len(self.fs)
        self.face_normals_up_to_date = False
        # if you autogenerate the vertex normal, using the faces, you need to
        # regenerate by setting self.gl.update_vertices
        self.gl.update_vertices = self.generate_normals

    def _set_faces(self, fs):
        """
        Define the shape faces

        fs: same as in face_props.
        """
        for f in fs:
            assert len(f) > 2, "A face should have at least 3 vertices"
        self.fs = fs
        self.faces_updated()

    @property
    def shape_colors(self):
        """Get the color data for this shape (see colors @ __init__)."""
        return self._shape_colors

    @shape_colors.setter
    def shape_colors(self, colors):
        """Set the face colours.

        colors: same as in __init__.
        """
        if colors[0] is not None:
            col_defs = colors[0]
        else:
            col_defs = tuple(self._shape_colors[0])
        if colors[1] is not None:
            face_cols = colors[1]
        else:
            face_cols = tuple(self._shape_colors[1])

        self._shape_colors = (col_defs, face_cols)
        self.no_of_cols = len(col_defs)
        self.col_range = range(self.no_of_cols)
        self._divide_col()
        assert self.no_of_cols > 0, f"Empty col_defs: {col_defs}"

        self.clean_up_colors()

    def clean_up_colors(self):
        """Remove unused colours and remove duplicates

        This will update
            - self.shape_colors
            - self.equal_colored_fs
            - self.no_of_cols
            - self.col_range
        """
        col_defs = self._shape_colors[0]
        face_cols = self._shape_colors[1]

        # Build all from scratch
        new_col_defs = []
        new_face_cols = []

        # Index is the same a colour index in col_defs
        # The list at that index gives all face indices with that colour.
        self.equal_colored_fs = []

        for face_i, col_i in enumerate(face_cols):
            col = col_defs[col_i]
            if col in new_col_defs:
                new_col_i = new_col_defs.index(col)
                self.equal_colored_fs[new_col_i].append(face_i)
            else:
                new_col_i = len(new_col_defs)
                new_col_defs.append(col)
                self.equal_colored_fs.append([face_i])
            new_face_cols.append(new_col_i)

        self._shape_colors = (tuple(new_col_defs), tuple(new_face_cols))
        self.no_of_cols = len(new_col_defs)
        self.col_range = range(self.no_of_cols)

    def update_face_with_col(self, face_i, new_col):
        """Update the face with index 'face_i' with the colour 'new_col'

        face_i: index of the face
        new_col: new RGB colour for the face to use
        """
        col_defs = list(self.shape_colors[0])
        face_cols = list(self.shape_colors[1])

        # update colour
        if new_col in col_defs:
            new_col_i = col_defs.index(new_col)
        else:
            new_col_i = len(col_defs)
            col_defs.append(new_col)
        face_cols[face_i] = new_col_i
        # This is needed since shape.shape_colors is not just an attribute, it is a setter
        self.shape_colors = (col_defs, face_cols)

    def remove_faces(self, indices):
        """Remove all faces with the specified indices"""
        fs = [face for i, face in enumerate(self.fs) if i not in indices]
        # Also remove these faces from face_colors
        face_colors = [
            col_i for i, col_i in enumerate(self._shape_colors[1]) if i not in indices
        ]
        self._shape_colors = (self._shape_colors[0], face_colors)
        self.clean_up_colors()
        self._set_faces(fs)

    def reverse_face(self, face_i):
        """Use reverse order for the face with face index face_i"""
        self.fs[face_i].reverse()

    @property
    def draw_faces(self):
        """Return whether the shape faces are drawn by OpenGL."""
        return self.gl.draw_faces

    @draw_faces.setter
    def draw_faces(self, draw):
        """
        Set whether the faces need to be drawn in gl_draw (or not).

        draw: optional argument that is True by default. Set to False to
              disable drawing of the faces.
        """
        self.gl.draw_faces = draw

    def generate_face_normal(self, f, normalise):
        """For the specified face return a face normal.

        f: the face (a list of vertex indices). Must at least contain 3 vertices.
        normalise: boolean stating whether to mormalise the normal

        The normal with point inwards of outwards depending on whether self.normal_direction is set
        to TRI_IN or TRI_OUT

        return: the normal
        """
        l = len(f)
        assert l > 2, "An face should at least have 2 vertices"
        if l < 3:
            assert False, "Normal for digons not implemented"
            # TODO: what to do here?
        normal = Triangle(self.vs[f[0]], self.vs[f[1]], self.vs[f[2]]).normal(normalise)
        if self.normal_direction in (TRI_OUT, TRI_IN):
            v0 = geomtypes.Vec3(self.vs[f[0]])
            outwards = v0.norm() < (v0 + normal).norm()
            if (outwards and self.normal_direction == TRI_IN) or (
                not outwards and self.normal_direction == TRI_OUT
            ):
                normal = -normal
        return normal

    def create_face_normals(self, normalise):
        """Create face normals and save in self.

        normalise: boolean stating whether to normalise the normals.

        return: none
        """
        if (
            not self.face_normals_up_to_date
            or self.face_normals_normalised != normalise
        ):
            self.face_normals = [
                self.generate_face_normal(f, normalise) for f in self.fs
            ]
            self.face_normals_up_to_date = True
            self.face_normals_normalised = normalise

    def create_vertex_normals(self, normalise, vs=None):
        """Create vertex normals and save in self.

        vs: and array with vertices to create normals for. Is not set, then self.vs is used.
        normalise: boolean stating whether to normalise the normals (refers mainly to edges).

        It will create the following attributes:
        normal_per_vertex: contains the normal per each vertex per face and vertex. The vertex
            normal for a face is the same as the face normal. The vertex normal for an edge is the
            vertex pointer. It relates to vertex_per_normal by using the same index.
        vertex_per_normal: contains the vertices per face and edge. It relates to normal_per_vertex
            by using the same index
        triangulated_faces_n_index: The faces triangulated. Each face is a list of triplets, one for
            each triangle. These triangles are supposed to be used with the stencil buffer. The
            indices of these faces refer to vertex_per_normal / normal_per_vertex and not to vs. The
            former contains one vertex for each face and one for the edges.
        edges_n_index: contains the edge indices where the indices aren't referring to self.es, but
            to vertex_per_normal / normal_per_vertex

        return: none
        """
        if vs is None:
            vs = self.vs
        self.create_face_normals(normalise)
        # only use a vertex once, since the normal can be different
        self.vertex_per_normal = []
        self.normal_per_vertex = []
        for face, normal in zip(self.fs, self.face_normals):
            self.normal_per_vertex.extend([normal for vi in face])
            self.vertex_per_normal.extend([geomtypes.Vec3(vs[vi][0:3]) for vi in face])
        counter = -1

        def inc():
            nonlocal counter
            counter += 1
            return counter

        face_per_normal_idx = [[inc() for i in face] for face in self.fs]
        self.triangulated_faces_n_index = self.triangulate(face_per_normal_idx)
        # Now for the edge vertices. Note that edge vertices aren't necessarily
        # part of the face vertices.
        edge_idx_offset = len(self.vertex_per_normal)
        self.vertex_per_normal.extend(vs)
        if normalise:
            for v in vs:
                self.normal_per_vertex.append(v.normalize())
        else:
            for v in vs:
                self.normal_per_vertex.append(v)
        self.edges_n_index = [old_v_idx + edge_idx_offset for old_v_idx in self.es]

    def create_edge_lengths(self, precision=12):
        """For each edge calculate the edge length.

        The edge lengths are save in a dictionary which is returned and also saved in
        self.len_to_edge. The dictionary maps different lengths (keys) onto edges; two-tuples
        consisting of two ordered vertex indices (values). returned.
        """
        len_to_edge = {}
        for ei in len(self.es):
            vi0 = self.es[ei]
            vi1 = self.es[ei + 1]
            if vi0 < vi1:
                t = (vi0, vi1)
            else:
                t = (vi1, vi0)
            l = (geomtypes.Vec3(self.vs[vi1]) - geomtypes.Vec3(self.vs[vi0])).norm()
            l = round(l, precision)
            try:
                len_to_edge[l].append(t)
            except KeyError:
                len_to_edge[l] = [t]
        self.len_to_edge = len_to_edge
        return len_to_edge

    def _get_dihedral_angles(self, precision=12):
        """Get all different dihedral angles.

        precision: number of decimals to take into account to interpret as unique angle

        return: a dictionary where the keys are the unique dihedral angles and the values are a list
        of edges, where each edge is a tuple with a pair of vertex indices.
        """
        self.create_face_normals(normalise=False)
        dihedral_to_edge = {}  # the result
        no_of_faces = len(self.fs)

        def add_dihedral_angle(face_idx, chk_face, cfi, edge, v0_chk_face_idx):
            """Add one dihedral angle to the global dihedral_to_edge

            face_idx: the index of the face under investigation
            chk_face: the face we are checking against holding a list of vertex indices
            cfi: the index of chk_face in the list of faces
            edge: an edge consisting of a pair vertex indices (in a tuple). The dihedral angle for
                this face will be added.
            v0_chk_face_idx: index of edge[0] in chk_face.

            return: None.
            """
            v0_idx, v1_idx = edge
            i_prev = v0_chk_face_idx - 1
            if i_prev < 0:
                i_prev = len(chk_face) - 1
            i_next = v0_chk_face_idx + 1
            if i_next >= len(chk_face):
                i_next = 0
            # if the vertex v0_idx - v1_idx is part of chk_face
            if v1_idx in (chk_face[i_prev], chk_face[i_next]):
                # found: add the angle and edge to dihedral_to_edge
                if v0_idx < v1_idx:
                    t = (v0_idx, v1_idx)
                else:
                    t = (v1_idx, v0_idx)
                angle = math.pi - self.face_normals[face_idx].angle(
                    self.face_normals[cfi]
                )
                angle = round(angle, precision)
                try:
                    dihedral_to_edge[angle].append(t)
                except KeyError:
                    dihedral_to_edge[angle] = [t]

        for face_idx, face in enumerate(self.fs):
            no_of_indices = len(face)
            for edge in [
                (v_idx, face[(i + 1) % no_of_indices]) for i, v_idx in enumerate(face)
            ]:
                for next_face_idx in range(face_idx + 1, no_of_faces):
                    chk_face = self.fs[next_face_idx]
                    try:
                        i = chk_face.index(edge[0])
                    except ValueError:
                        i = -1
                    if i >= 0:
                        add_dihedral_angle(face_idx, chk_face, next_face_idx, edge, i)
        return dihedral_to_edge

    def _divide_col(self):
        """
        Divide the specified colours over the faces.

        This function wraps the divide_col function and handles the trivial
        cases for which there is only one colour of for which there are more
        colours than faces. These trivial cases do not need to be implemented by
        every descendent.
        """
        if len(self._shape_colors[1]) != self.no_of_fs:
            if self.no_of_cols == 1:
                self._shape_colors = (
                    self._shape_colors[0],
                    [0 for i in range(self.no_of_fs)],
                )
            elif self.no_of_cols and self.no_of_cols < self.no_of_fs:
                self.divide_col()
            else:
                self._shape_colors = (self._shape_colors[0], list(range(self.no_of_fs)))
            assert len(self._shape_colors[1]) == self.no_of_fs
        # generate an array with equal coloured faces:
        # Index is the same a colour index in col_defs
        # The list at that index gives all face indices with that colour.
        self.equal_colored_fs = [[] for col in range(self.no_of_cols)]
        for i in range(self.no_of_fs):
            self.equal_colored_fs[self._shape_colors[1][i]].append(i)

    def divide_col(self):
        """
        Divide the specified colours over the isometries.

        This function should actually be implemented by a descendent, so that
        the colours can be divided according to the symmetry. This function
        just repeats the colours until the length is long enough.
        The amount of colours should be less than the nr of isomentries.
        """
        div = self.no_of_fs // self.no_of_cols
        mod = self.no_of_fs % self.no_of_cols
        face_cols = []
        all_color_idx = list(range(self.no_of_cols))
        for _ in range(div):
            face_cols.extend(all_color_idx)
        face_cols.extend(list(range(mod)))
        self._shape_colors = (self._shape_colors[0], face_cols)

    def transform(self, trans):
        """Transform the model using the specified instance of a geomtypes.Trans3 object."""
        self.vs = [trans * v for v in self.vs]
        self.gl.update_vertices = True

    def scale(self, factor):
        """Scale the vertices of the object."""
        self.vs = [factor * v for v in self.vs]
        self.gl.update_vertices = True

    def zoom(self, factor):
        """Use the specified factor to zoom in when drawing the 3D object.

        This is used for scaling polychora cells
        """
        self.zoom_factor = factor
        self.gl.update_vertices = True

    def calc_fs_gravity(self):
        """For each face calculate the gravity point

        The gravity point is saved in self.fs_gravity
        """
        self.fs_gravity = [
            reduce(lambda t, i: t + self.vs[i], f, vec(0, 0, 0)) / len(f)
            for f in self.fs
        ]

    def calc_sphere_radii(self, precision=12):
        """Calculate the radii for the circumscribed, inscribed and mid sphere(s)"""
        # calculate the circumscribed spheres:
        self.spheres_radii.precision = precision
        s = {}
        for v in self.vs:
            r = round(v.norm(), precision)
            try:
                cnt = s[r]
            except KeyError:
                cnt = 0
            s[r] = cnt + 1
        self.spheres_radii.circumscribed = s
        s = {}
        for i in range(0, len(self.es), 2):
            v = (self.vs[self.es[i]] + self.vs[self.es[i + 1]]) / 2
            r = round(v.norm(), precision)
            try:
                cnt = s[r]
            except KeyError:
                cnt = 0
            s[r] = cnt + 1
        self.spheres_radii.mid = s
        s = {}
        try:
            self.fs_gravity
        except AttributeError:
            self.calc_fs_gravity()
        for g in self.fs_gravity:
            r = round(g.norm(), precision)
            try:
                cnt = s[r]
            except KeyError:
                cnt = 0
            s[r] = cnt + 1
        self.spheres_radii.inscribed = s

    def gl_init(self):
        """
        Initialise OpenGL for specific shapes

        Enables a derivative to use some specific OpenGL settings needed for
        this shape. This function is called in gl_draw for the first time gl_draw
        is called.
        """
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glDisable(GL.GL_CULL_FACE)

        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_BLEND)

        self.gl_initialised = True

    def gl_draw(self):
        """wrap _gl_draw to be able to catch OpenGL errors"""
        if self.vs == []:
            return
        if not self.gl_initialised:
            self.gl_init()

        # Check if unity matrix?
        GL.glPushMatrix()

        try:
            self._gl_draw()
        except GL.OpenGL.error.Error:
            logging.error("OpenGL Error occurred. Did you define PYOPENGL_PLATFORM?")
        except:
            GL.glPopMatrix()
            raise

        GL.glPopMatrix()

    def _gl_draw(self):
        """
        Draw the base element according to the definition of the vs, es, fs and
        colour settings.

        Set self.vertex_props, and edge_props and face_props to specify how and whether to draw
        the vertices, edges and faces respectively.
        """
        GL.glMultMatrixd(self.orientation.glMatrix())
        if self.gl.update_vertices:
            # calculate the gravitational centre. Only calculate the vertices
            # that are used:
            if geomtypes.FloatHandler.eq(self.zoom_factor, 1.0):
                vs = self.vs
            else:
                v_usage = glue.getVUsageIn1D(self.vs, self.es)
                v_usage = glue.getVUsageIn2D(self.vs, self.fs, v_usage)
                g = vec(0, 0, 0)
                total = 0
                for v_idx in self.vertex_range:
                    g = g + v_usage[v_idx] * geomtypes.Vec3(self.vs[v_idx])
                    total += v_usage[v_idx]
                if total != 0:
                    g = g / total
                vs = [self.zoom_factor * (geomtypes.Vec3(v) - g) + g for v in self.vs]

            # At least on Ubuntu 8.04 conversion is not needed
            # On windows and Ubuntu 9.10 the vs cannot be an array of vec3...
            if not self.generate_normals:
                try:
                    if not gl_vertex_pointer(vs):
                        return
                    normals = self.ns
                except TypeError:
                    vs = [[v[0], v[1], v[2]] for v in vs]
                    logging.info("gl_draw: converting vs(ns); vec3 type not accepted")
                    if not gl_vertex_pointer(vs):
                        return
                    normals = [[v[0], v[1], v[2]] for v in self.ns]
                if normals != []:
                    assert len(normals) == len(
                        vs
                    ), "the normal vector array 'normals' should have as many normals as vertices."
                    gl_normal_pointer(normals)
                    self.saved_ns = normals
                else:
                    gl_normal_pointer(vs)
                    self.saved_ns = vs
            elif self.ns != [] and len(self.ns) == len(vs):
                try:
                    if not gl_vertex_pointer(vs):
                        return
                    normals = self.ns
                except TypeError:
                    vs = [[v[0], v[1], v[2]] for v in vs]
                    logging.info("gl_draw: converting vs(ns); vec3 type not accepted")
                    if not gl_vertex_pointer(vs):
                        return
                    normals = [[n[0], n[1], n[2]] for n in self.ns]
                gl_normal_pointer(normals)
                self.saved_ns = normals
            else:
                self.create_vertex_normals(True, vs)
                if self.vertex_per_normal:
                    if not gl_vertex_pointer(self.vertex_per_normal):
                        return
                gl_normal_pointer(self.normal_per_vertex)
                self.saved_ns = self.normal_per_vertex
                vs = self.vertex_per_normal
            self.gl.update_vertices = False
            self.saved_vs = vs
        else:
            if self.gl.force_set_vs:
                if not gl_vertex_pointer(self.saved_vs):
                    return
                gl_normal_pointer(self.saved_ns)
        # VERTICES
        if self.gl.sphere_vertices:
            GL.glColor(
                self.gl.vertex_col[0] / 255,
                self.gl.vertex_col[1] / 255,
                self.gl.vertex_col[2] / 255,
            )
            for i in self.vertex_range:
                self.gl.sphere.draw(self.vs[i])
        # EDGES
        if self.gl.draw_edges:
            if self.generate_normals and (
                self.ns == [] or len(self.ns) != len(self.vs)
            ):
                es = self.edges_n_index
                vs = self.vertex_per_normal
            else:
                es = self.es
                vs = self.vs
            GL.glColor(
                self.gl.edge_col[0] / 255,
                self.gl.edge_col[1] / 255,
                self.gl.edge_col[2] / 255,
            )
            if self.gl.cylindrical_edges:
                # draw edges as cylinders
                for i in range(0, len(self.es), 2):
                    self.gl.cyl.draw(v0=vs[es[i]], v1=vs[es[i + 1]])
            else:
                # draw edges as lines
                GL.glPolygonOffset(1.0, 3.0)
                GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
                gl_draw_elements(GL.GL_LINES, es)
                GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)

        # FACES
        if self.gl.draw_faces:
            for col_idx in self.col_range:
                c = [chn / 255 for chn in self._shape_colors[0][col_idx]]
                if len(c) == 3:
                    GL.glColor(c[0], c[1], c[2])
                else:
                    a = max(c[3], 0)
                    a = min(a, 255)
                    GL.glColor(c[0], c[1], c[2], a)
                for face_idx in self.equal_colored_fs[col_idx]:
                    triangles = self.triangulated_faces_n_index[face_idx]
                    # Note triangles is a flat (ie 1D) array
                    if len(triangles) == 3:
                        gl_draw_elements(GL.GL_TRIANGLES, triangles)
                    else:
                        # TODO: This part belongs to a GLinit:
                        GL.glClearStencil(0)
                        stencil_bits = GL.glGetIntegerv(GL.GL_STENCIL_BITS)
                        assert (
                            stencil_bits > 0
                        ), "Only triangle faces are supported, since there is no stencil bit"
                        # << TODO: end part that belongs to a GLinit
                        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
                        # use stecil buffer to triangulate.
                        GL.glColorMask(
                            GL.GL_FALSE, GL.GL_FALSE, GL.GL_FALSE, GL.GL_FALSE
                        )
                        GL.glDepthMask(GL.GL_FALSE)
                        # Enable Stencil, always pass test
                        GL.glEnable(GL.GL_STENCIL_TEST)
                        # always pass stencil test
                        GL.glStencilFunc(GL.GL_ALWAYS, 1, 1)
                        # stencil fail: don't care, never fails
                        # z-fail: zero
                        # both pass: invert stencil values
                        GL.glStencilOp(GL.GL_KEEP, GL.GL_ZERO, GL.GL_INVERT)
                        # Create triangulated stencil:
                        gl_draw_elements(GL.GL_TRIANGLES, triangles)
                        # Reset colour mask and depth settings.
                        GL.glDepthMask(GL.GL_TRUE)
                        GL.glColorMask(GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE)
                        # Draw only where stencil equals 1 (masked to 1)
                        # GL_INVERT was used, i.e. in case of e.g. 8 bits the value is
                        # either 0 or 0xff, but only the last bit is checked.
                        GL.glStencilFunc(GL.GL_EQUAL, 1, 1)
                        # make stencil read only:
                        GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)
                        # Now, write according to stencil
                        gl_draw_elements(GL.GL_TRIANGLES, triangles)
                        # ready, disable stencil
                        GL.glDisable(GL.GL_STENCIL_TEST)

    def to_off(
        self, precision=geomtypes.FLOAT_OUT_PRECISION, info=False, color_floats=False
    ):
        """Return a representation of the object in the 3D 'OFF' file format.

        precision: the precision that will be used for printing the coordinates
                   of the vertices.
        color_floats: whether to export the colours as floating point numbers
                      between 0 and 1. If False an integer 0 to 255 is used.
        """

        def w(s1):
            nonlocal s
            return f"{s}{s1}\n"

        s = ""
        s = w("OFF")
        s = w("#")
        s = w(f"# {self.name}")
        s = w("#")
        s = w("# file generated with python script by Marcel Tunnissen")
        if info:
            self.calc_sphere_radii()
            s = w(f"# inscribed sphere(s)    : {self.spheres_radii.inscribed}")
            s = w(f"# mid sphere(s)          : {self.spheres_radii.mid}")
            s = w(f"# circumscribed sphere(s): {self.spheres_radii.circumscribed}")
            dihedral_to_angle = self._get_dihedral_angles()
            for a, es in dihedral_to_angle.items():
                s = w(
                    f"# Dihedral angle: {geomtypes.f2s(a, precision)} rad "
                    f"({geomtypes.f2s(a * RAD2DEG, precision)} degrees) for {len(es)} edges"
                )
                if len(es) > 2:
                    s = w(f"#                 E.g. {es[0]}, {es[1]}, {es[2]} etc")
            len_to_edge = self.create_edge_lengths()
            for l, es in len_to_edge.items():
                s = w(f"# Length: {geomtypes.f2s(l, precision)} for {len(es)} edges")
                if len(es) > 2:
                    s = w(f"#         E.g. {es[0]}, {es[1]}, {es[2]}, etc")
        s = w("# Vertices Faces Edges")
        no_of_faces = len(self.fs)
        no_of_edges = len(self.es) // 2
        s = w(f"{len(self.vs)} {no_of_faces} {no_of_edges}")
        s = w("# Vertices")
        for v in self.vs:
            with geomtypes.FloatHandler(precision):
                s = w(
                    f"{geomtypes.RoundedFloat(v[0])} "
                    f"{geomtypes.RoundedFloat(v[1])} "
                    f"{geomtypes.RoundedFloat(v[2])}"
                )
        s = w("# Sides and colours")
        # self._shape_colors[1] = [] : use self._shape_colors[0][0]
        # self._shape_colors[1] = [c0, c1, .. cn] where ci is an index i
        #                     self._shape_colors[0]
        #                     There should be as many colours as faces.
        if len(self._shape_colors[0]) == 1:
            one_col = True
            color = self._shape_colors[0][0]
        else:
            one_col = False
            assert len(self._shape_colors[1]) == len(self.fs)

        def face_str(face):
            """convert face to string in off-format."""
            s = f"{len(face)} "
            for fi in face:
                s += f" {fi}"
            if color_floats:
                s += f"  {color[0] / 255:g} {color[1] / 255:g} {color[2] / 255:g}"
            else:
                s += f"  {color[0]} {color[1]} {color[2]}"
            return s

        if one_col:
            for face in self.fs:
                # the lambda w didn't work: (Ubuntu 9.10, python 2.5.2)
                s += f"{face_str(face)}\n"
        else:
            self.create_face_normals(normalise=True)
            for i in range(no_of_faces):
                face = self.fs[i]
                color = self._shape_colors[0][self._shape_colors[1][i]]
                s = f"{s}{face_str(face)}\n"
                face_normal = self.face_normals[i]
                face_idx_str = f"{face_normal[0]} {face_normal[1]} {face_normal[2]}"
                if info:
                    s = w(f"# face normal: {face_idx_str}")
        if info:
            for i in range(no_of_edges):
                s = w(f"# edge: {self.es[2 * i]} {self.es[2 * i + 1]}")
        s = w("# END")
        return s

    @staticmethod
    def _get_face_plane(vs, face):
        """
        Define a Plane object from a face

        vs: the 3D vertex coordinates
        face: the indices in vs that form the face.
        Returns None if the vertices do not define a plane.
        """
        assert len(face) > 2, "a face should at least be a triangle"
        plane = None
        plane_found = False
        fi_0 = 1
        fi_1 = 2
        while not plane_found:
            try:
                plane = Plane(vs[face[0]], vs[face[fi_0]], vs[face[fi_1]])
                plane_found = True
            except (ValueError, AssertionError):
                fi_1 += 1
                if fi_1 >= len(face):
                    fi_0 += 1
                    fi_1 = fi_0 + 1
                    if fi_1 >= len(face):
                        logging.info("Ignoring degenerate face (line or point?)")
                        break
        return plane

    def _merge_faces_sharing_plane(self, face_indices):
        """Merge face lying in one plane to one compound of faces.

        Faces that don't share a plane will become a compound of one face

        face_indices: a list of face indices, where an index refers to self.fs

        return: a list for face compounds where each elements consists of two elements:
            1. a list of faces (where each face is a list for vertex indices)
            2. the plane (an object of class Plane) the face is lying in.
        """
        result = []

        # Calc all face planes and ignore "fake" faces:
        faces = []
        for i in face_indices:
            face = self.fs[i]
            face_plane = self._get_face_plane(self.vs, face)
            if face_plane is None:
                continue  # not a face
            if face_plane.normal is None:
                continue  # not a face
            faces.append((face, face_plane))

        for face, plane in faces:
            found = False
            logging.debug(
                "checking plane %s for face %s of len %d", plane, face, len(face)
            )
            for existing_face_compound, existing_plane in result:
                if plane == existing_plane:
                    existing_face_compound.append(face)
                    logging.debug("FOUND")
                    found = True
                    break
            if not found:
                logging.debug("Adding new plane")
                result.append(([face], plane))
        return result

    def _rotate_shape_to_hor_plane(self, face_plane):
        """
        Rotate the vertices so that the specified plane is parallel to the XOY plane

        face_plane: an object of class Plane.

        return: a tuple with the updated shape vertices and the same vertices where the z-coordinate
        is removed.
        """
        # Find out how to rotate the shape such that the norm of the base face
        # is parallel to the z-axis to work with a 2D situation:
        # Rotate around the cross product of z-axis and norm
        # with an angle equal to the dot product of the normalised vectors.
        z_axis = vec(0, 0, 1)
        to_2d_angle = geomtypes.RoundedFloat(math.acos(z_axis * face_plane.normal))
        if to_2d_angle in (2 * math.pi, -2 * math.pi, math.pi, -math.pi):
            to_2d_angle = geomtypes.RoundedFloat(0.0)
        if to_2d_angle != 0:
            logging.debug("to_2d_angle: %f", to_2d_angle)
            to_2d_axis = face_plane.normal.cross(z_axis)
            logging.debug("to_2d_axis: %s", to_2d_axis)
            rot_mat = geomtypes.Rot3(angle=to_2d_angle, axis=to_2d_axis)
            vs = [rot_mat * v for v in self.vs]
        else:
            vs = self.vs[:]

        return vs

    # TODO: Instead of face, vs perhaps you should just have a list of vertices for face
    @staticmethod
    def _calc_intersection(intersecting_face, face_plane, hor_plane, z, vs):
        """Calculate the intersections for a face with a horizontal plane

        The result will consist of line segments that are part of the face. For a convex face there
        is only one segment, but for a concave there can be more than one.

        intersecting_face: the face to intersect with the horizontal plane. It is a list of vertex
            indices.
        face_plane: the Plane object in which face is part of.
        hor_plane: the Plane object that defines the horizontal plane to intersect with.
        z: the z-coordinate for the horizontal plane.
        vs: the vertex indices as used for the face.

        return: a tuple with a geom_2d.Line object and a list of line factors that form line
            segments of where the face intersects the horizontal plane. Each segment is represented
            by one pair of factors (2-tuple).
        """
        line_3d = hor_plane.intersect_with_plane(face_plane)
        if line_3d is None:
            logging.debug("No intersection for face")
        else:
            logging.debug(
                "intersecting horizontal plane %s with %s", face_plane, line_3d
            )
            assert geomtypes.RoundedFloat(line_3d.v[2]) == 0, (
                "all intersection lines should be paralell to z = 0, "
                f"but z varies with {line_3d.v[2]} (margin: {geomtypes.FloatHandler.margin})"
            )
            assert geomtypes.RoundedFloat(line_3d.p[2]) == z, (
                f"all intersection lines should ly on z=={z}, "
                f"but z differs {z - line_3d.p[2]} "
                f"(margin: {geomtypes.FloatHandler.margin})"
            )

            line_2d = geom_2d.Line(line_3d.p[:2], v=line_3d.v[:2])
            # Get the line_2d elements where it intersects the face. One can do this as follows
            #  - translate face plane to XOY (T1)
            #  - translate to rotate around the line (put a point of line in origin) (T2)
            #  - rotate around line so the the plane normal is parallel to the z-axis
            #  - translate the face back within the XoY plane (-T2)
            #  - intersect in 2D
            # However this makes the algorithm very slow. Is is quicker just to project the whole
            # face orthogonally to the XoY plane. The same line factors will be obtained, unless the
            # face is orthogonal, or almost for precision reasons, to the XoY plane.
            z_axis = vec(0, 0, 1)
            with geomtypes.FloatHandler(1):
                simplify = face_plane.normal != z_axis
            if simplify:
                vs_2d = [v[:2] for v in vs]
            else:
                # translate with T1 and T2:
                vs = [c - line_3d.p for c in vs]
                # rotate to make plane horizontal and translate back (-T2)
                to_hor_angle = geomtypes.RoundedFloat(
                    math.acos(z_axis * face_plane.normal)
                )
                rot_mat = geomtypes.Rot3(angle=to_hor_angle, axis=line_3d.v)
                t_back = line_3d.p[:]
                vs_2d = [geomtypes.Vec((rot_mat * v)[:2]) + t_back for v in vs]

            polygon_2d = geom_2d.Polygon(vs_2d, intersecting_face)
            line_factors = line_2d.intersect_polygon_get_factors(polygon_2d)
            logging.debug("line factors %s", line_factors)
            if line_factors != []:
                return (line_2d, line_factors)
        return ()

    @staticmethod
    def _combine_intersections_to_faces(
        intersection_lines, faces_to_intersect_with, vs
    ):
        """Combine intersection segments with faces to intersect with.

        With the line segments that are valid segments for for the face(s) that are intersecting the
        horizontal plane, check how much of these segments are valid segments in the face(s) we are
        intersecting with, i.e. the face(s) in that horizontal plane.

        intersection_lines: an list of tuples consisting of a geom_2d.Line object and a list of line
            factors that are valid factors for the faces that intersect the specified faces
        faces_to_intersect_with: the faces that are intersected with the intersection_lines.
        vs: the vertex indices as used for the face.

        return: An updated list of tuples consisting of a geom_2d.Line object and a list of line
            factors.
        """
        # for each intersecting line segment:
        resulting_intersections = []
        for i, (line_2d, line_factors_0) in enumerate(intersection_lines):
            logging.debug("phase 2: check intersection %d", i)
            # line_2d: the line object representing the line of intersection
            # line_factors_0: the line segments (factors) valid for the intersecting face
            # line_factors_1: the line segments (factors) valid for the face to intersect with
            # updated_factors: the valid factors resulting in combining the above.
            new_factors = []
            for face_to_intersect_with in faces_to_intersect_with:
                polygon_2d = geom_2d.Polygon(
                    [v[:2] for v in vs], face_to_intersect_with
                )
                line_factors_1 = line_2d.intersect_polygon_get_factors(polygon_2d)
                logging.debug("line_factors_1 %s", line_factors_1)
                # Now combine the results of line_factors_0 and line_factors_1:
                # Only keep intersections that fall within 2 segments for
                # both line_factors_0 and line_factors_1.
                i_segment_0 = 0  # segment number in line_factors_0
                i_segment_1 = 0  # segment number in line_factors_1
                select_segment_0 = True
                select_segment_1 = True

                while i_segment_0 < len(line_factors_0) and i_segment_1 < len(
                    line_factors_1
                ):
                    if select_segment_0:
                        f0 = line_factors_0[i_segment_0][0]
                        f1 = line_factors_0[i_segment_0][1]
                        select_segment_0 = False
                    if select_segment_1:
                        g0 = line_factors_1[i_segment_1][0]
                        g1 = line_factors_1[i_segment_1][1]
                        select_segment_1 = False
                    # Note that always holds f0 < f1 and g0 < g1
                    if f1 <= g0:
                        # f0 - f1  g0 - g1
                        select_segment_0 = True
                    elif g1 <= f0:
                        # g0 - g1  f0 - f1
                        select_segment_1 = True
                    elif f0 <= g0:
                        if f1 <= g1:
                            # f0  g0 - f1  g1
                            new_factors.append((g0, f1))
                            select_segment_0 = True
                        else:
                            # f0  g0 - g1  f1
                            new_factors.append((g0, g1))
                            select_segment_1 = True
                    else:
                        # g0<f0<g1 (and g0<f1)
                        if f1 <= g1:
                            # g0  f0 - f1  g1
                            new_factors.append((f0, f1))
                            select_segment_0 = True
                        else:
                            # g0  f0 - g1  f1
                            new_factors.append((f0, g1))
                            select_segment_1 = True
                    if select_segment_0:
                        i_segment_0 += 1
                    if select_segment_1:
                        i_segment_1 += 1
            resulting_intersections.append((line_2d, new_factors))
        return resulting_intersections

    def _intersect_with_face_in_hor_plane(self, vs, compound_face, z):
        """
        Intersect all faces with a face in an horizontal plane

        vs: the list of vertices for an shape with an updated orientation so that the compound face
            is in a horizontal plane.
        comound_face: a list of faces. Each face is a list of vertex indices. The faces should all
            ly in the horizontal plane (with the orientatoin specified by vs)
        z: the z-value of the horizontal plane to intersect with.

        return: a tuple of a points list and a polygons list. Each point consists of an X, Y
            coordinate in the plane, while a polygon is a list of indinces in the points list. A
            polygon might also just be an egde.
        """
        hor_plane = PlaneFromNormal(vec(0, 0, 1), vec(0, 0, z))
        logging.debug("hor_plane %s", hor_plane)

        # split faces into
        # 1. faces that ly in the plane: faces_to_intersect_with, i.e. the other faces will be
        #    intersected with these.
        # 2. faces that share line segment(s) with this plane: intersection faces. Only save the
        #    line segments data of these.
        points = [[v[0], v[1]] for v in vs]
        polygons = []
        faces_to_intersect_with = []
        intersection_lines = []
        for intersecting_face in self.fs:
            logging.debug(
                "Intersecting face[%d] = %s with the compound face",
                self.fs.index(intersecting_face),
                intersecting_face,
            )
            intersecting_plane = self._get_face_plane(vs, intersecting_face)

            calc_intersection = True
            # check whether the intersection face is in the plane
            if intersecting_plane == hor_plane:
                faces_to_intersect_with.append(intersecting_face)
                polygons.append(intersecting_face)
                logging.debug("Intersecting face shares the plane")
                calc_intersection = False
            else:
                # Check whether they share an edge
                l = len(intersecting_face)
                for p in range(l):
                    for face in compound_face:
                        if intersecting_face[p] in face:
                            q = p + 1
                            if q == l:
                                q = 0
                            if intersecting_face[q] in face:
                                p_idx = face.index(intersecting_face[p])
                                q_idx = face.index(intersecting_face[q])
                                delta = abs(p_idx - q_idx)
                                if delta in (1, len(face) - 1):
                                    calc_intersection = False
                                    logging.debug("Intersecting face shares an edge")
                                    break

            # line of intersection:
            if calc_intersection:
                # TODO: I don't like this many parameters:
                intersection_line = self._calc_intersection(
                    intersecting_face, intersecting_plane, hor_plane, z, vs
                )
                if intersection_line:
                    intersection_lines.append(intersection_line)

        intersection_lines = self._combine_intersections_to_faces(
            intersection_lines, faces_to_intersect_with, vs
        )

        last_point = len(points) - 1
        for line_2d, line_factors in intersection_lines:
            for t0, t1 in line_factors:
                points.append(line_2d.get_point(t0))
                points.append(line_2d.get_point(t1))
                last_point += 2
                polygons.append([last_point - 1, last_point])

        return points, polygons

    def to_postscript(
        self,
        face_indices=None,
        scaling=1,
        precision=7,
        page_size=PS.PageSizeA4,
    ):
        """Print in PS For each face where the other faces meet that face.

        Returns a string in PS format that shows the pieces of faces that can
        be used for constructing a physical model of the object.

        The function will for each face check whether it intersects another
        face. By these intersections the face is divided into pieces. All pieces
        are printed, not only the ones that are visible from the outside.

        To get correct results and to prevent asserts it is wise to wrap this method in a
        FloatHandler statement as shown below. It shows an example of using 8 digits when comparing
        floats. Note this is independent of the precision parameter.
            with geomtypes.FloatHandler(precision=8):
                object.to_postscript(..)

        face_indices: an array of faces for which the pieces should be printed. Since many objects
            have symmetry it is not needed to calculate the pieces for each face.
        scaling: All pieces in all faces are scaled by a certain factor in the resulting PS string.
            This factor can be adjusted later in the file itself (after printing the string to a
            file).
        precision: The amount of decimals to use fir floating point numbers in the output string.
        """
        if not face_indices:
            face_indices = list(range(len(self.fs)))
        ps_doc = PS.doc(title=self.name, pageSize=page_size)
        if logging.root.level < logging.DEBUG:
            for i, vertex in enumerate(self.vs):
                logging.debug("V[%d] = %s", i, vertex)

        compound_faces = self._merge_faces_sharing_plane(face_indices)

        for i, (compound_face, face_plane) in enumerate(compound_faces):
            logging.debug("checking face %d (of %d)", i + 1, len(compound_faces))

            vs = self._rotate_shape_to_hor_plane(face_plane)

            # set z-value for the z-plane, ie plane of intersection
            # TODO: better would be to take the average of all z coords
            z_base_plane = vs[compound_face[0][0]][2]
            logging.debug("z_base_face = %s", z_base_plane)

            points_2d, lines_to_draw = self._intersect_with_face_in_hor_plane(
                vs, compound_face, z_base_plane
            )

            ps_doc.addLineSegments(points_2d, lines_to_draw, scaling, precision)

        return ps_doc.toStr()

    def get_dome(self, level=2):
        """Change the shape towards into a dome shaped model

        This is done by calculating the outer sphere (through the vertices) and projecting parts of
        the shape from the middle onto this sphere.

        level: for level 1 the gravitation centre of each is projected on to the sphere; for level 2
        edge centres are mapped onto the sphere.
        """
        shape = None
        # check if level is in supported domain
        if level < 1 or level > 2:
            return shape
        cols = self.face_props["colors"]
        vs = self.vs[:]
        no_of_vs_org = len(self.vs)
        try:
            self.fs_gravity
        except AttributeError:
            self.calc_fs_gravity()
        try:
            outer_radii = self.spheres_radii.circumscribed
        except AttributeError:
            self.calc_sphere_radii()
            outer_radii = self.spheres_radii.circumscribed
        radius = reduce(max, iter(outer_radii.keys()))
        fs = []
        col_indices = []

        def add_projected_vs(extra_vs):
            """Add extra vertices to the vertex array."""
            # func global vs, radius
            vs.extend([radius * x.normalize() for x in extra_vs])

        def dome_level_1(f, i):
            # return extra_fs
            # func global no_of_vs_org, cols
            # assumes that the gravity centres will be added to vs in face order
            # independently.
            l = len(f)
            return [[i + no_of_vs_org, f[j], f[(j + 1) % l]] for j in range(l)]

        def dome_level_2(f):
            # f can only be a triangle: no check
            # return (extra_vs, extra_fs) tuple
            # func global: vs
            extra_vs = []
            extra_vs = [(vs[f[i]] + vs[f[(i + 1) % 3]]) / 2 for i in range(3)]
            v_idx_offset = len(vs)
            extra_fs = [
                [v_idx_offset, v_idx_offset + 1, v_idx_offset + 2],
                [f[0], v_idx_offset, v_idx_offset + 2],
                [f[1], v_idx_offset + 1, v_idx_offset],
                [f[2], v_idx_offset + 2, v_idx_offset + 1],
            ]
            return (extra_vs, extra_fs)

        for i, f in enumerate(self.fs):
            if level == 1:
                extra_fs = dome_level_1(f, i)
                # add the gravity centres as assumed by dome_level_1:
                add_projected_vs(self.fs_gravity)
            else:
                l = len(f)
                if l == 3:
                    extra_vs, extra_fs = dome_level_2(f)
                    add_projected_vs(extra_vs)
                elif l > 3:
                    tmp_fs = dome_level_1(f, i)
                    # add the gravity centres as assumed by dome_level_1:
                    add_projected_vs(self.fs_gravity)
                    extra_fs = []
                    for sf in tmp_fs:
                        extra_vs, sx_fs = dome_level_2(sf)
                        add_projected_vs(extra_vs)
                        extra_fs.extend(sx_fs)
            fs.extend(extra_fs)
            col_indices.extend([cols[1][i] for j in range(len(extra_fs))])
        shape = SimpleShape(vs, fs, [], colors=(cols[0], col_indices))
        shape.regen_edges()
        return shape


class CompoundShape(base.Orbitit):
    """
    The class describes a shape that is the result of combining more than one
    SimpleShapes. The resulting shape can be treated as one, e.g. it can be
    exported as one 'OFF' file.
    """

    def __init__(
        self,
        shapes,
        regen_edges=True,
        name="CompoundShape",
    ):
        """
        shapes: a list of SimpleShape objects of which the shape is a compound.
        """
        self.name = name
        self.merge_needed = False
        # This is save so heirs can still use repr_dict from this class
        self.json_class = CompoundShape
        self.set_shapes(shapes)
        self.merged_shape = None
        if regen_edges:
            self.regen_edges()

    def __repr__(self):
        """
        Returns a python string that can be interpreted by Python for the shape
        """
        if len(self._shapes) == 1:
            return repr(self._shapes[0])
        class_name = base.find_module_class_name(self.__class__, __name__)
        s = indent.Str(f"{class_name}(\n")
        s = s.add_incr_line("shapes=[")
        s.incr()
        s = s.glue_line(
            ",\n".join(repr(shape).reindent(s.indent) for shape in self._shapes)
        )
        s = s.add_decr_line("],")
        s = s.add_line(f'name="{self.name}"')
        s = s.add_decr_line(")")
        if __name__ != "__main__":
            s = s.insert(f"{__name__}.")
        return s

    def __iter__(self):
        """Iterate through all shapes."""
        return iter(self._shapes)

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        return {
            "class": base.class_to_json[self.json_class],
            "data": {
                "name": self.name,
                "shapes": [s.repr_dict for s in self.shapes],
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        """Create object from a dictionary created by repr_dict."""
        return cls(
            shapes=[
                base.json_to_class[s["class"]].from_json_dict(s) for s in data["shapes"]
            ],
            name=data["name"],
        )

    def save_file(self, fd):
        """
        Save a shape in a file descriptor

        The caller still need to close the filde descriptor afterwards
        """
        save_file(fd, self)

    def add_shape(self, shape):
        """
        Add shape 'shape' to the current compound.
        """
        shape.gl.force_set_vs = True
        self._shapes.append(shape)
        if len(self._shapes) > 1:
            self._shapes[-1].generate_normals = self._shapes[0].generate_normals
        self.merge_needed = True

    def gl_force_set_vs(self, do):
        """
        Force to set the vertices in OpenGL, independently on the updated vertices flag.

        Normally the vertices in OpenGL are only reprogrammed if the vertices were updated, but
        setting this flag will always reprogram the vertices.
        """
        for shape in self._shapes:
            shape.gl_force_set_vs(do)

    @property
    def shapes(self):
        """Return all shapes of this compound shape"""
        return self._shapes

    def set_shapes(self, shapes):
        """
        Set the shapes all at once.

        Note: you need to make sure yourself to have the generate_normals set
        consistently for all shapes.
        """
        self._shapes = shapes
        self.gl_force_set_vs(True)
        self.merge_needed = True

    def merge_shapes(self):
        """Using the current array of shapes as defined in _shapes,
        initialise this object as a simple Shape.

        The function will create one vs, fs, and es from the current definition
        of _shapes and will initialise this object as a SimpleShape.
        """
        vs = []
        fs = []
        es = []
        ns = []
        col_defs = []
        col_idx = []
        for s in self._shapes:
            vs_offset = len(vs)
            col_offset = len(col_defs)
            s = s.simple_shape
            # Apply shape orientation here, needed, since the can be different
            # for the various shapes
            for v in s.vs:
                vs.append(s.orientation * v)
            for v in s.ns:
                ns.append(s.orientation * v)
            # offset all faces:
            fs.extend([[i + vs_offset for i in f] for f in s.fs])
            es.extend([i + vs_offset for i in s.es])
            col_defs.extend(s.shape_colors[0])
            col_idx.extend([i + col_offset for i in s.shape_colors[1]])
        self.merged_shape = SimpleShape(
            vs=vs, fs=fs, es=es, ns=ns, colors=(col_defs, col_idx), name=self.name
        )
        self.merge_needed = False

    @property
    def simple_shape(self):
        """Return the compound shape as a simple merged and flat shape"""
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape

    def clean_shape(self, precision):
        """Return a new shape for which vertices are merged and degenerated faces are deleted.

        The shape will not have any edges.

        precision: number of decimals to consider when deciding whether two floating point numbers
            are equal.
        """
        self.simple_shape.clean_shape(precision)

    def gl_draw(self):
        """Draws the compound shape as compound shape

        If you want to draw it as one, draw the SimpleShape instead
        """
        for shape in self._shapes:
            shape.gl_draw()

    def regen_edges(self):
        """Regenerate the edges of the shape."""
        for shape in self._shapes:
            shape.regen_edges()
        self.merge_needed = True

    @property
    def vertex_props(self):
        """Return a dictionary of the vertex properties of the compound

        See setter what to expect.
        """
        # Note: cannot use the megedShape, since the vs is not an array of vs
        d = self._shapes[0].vertex_props
        return {
            "vs": self.vs,
            "radius": d["radius"],
            "color": d["color"],
            "ns": self.ns,
        }

    @vertex_props.setter
    def vertex_props(self, props):
        """Set the vertex properties for a whole compound shape at once

        The properties can be specified as a dictionary with the following keys:
        vs: This is an array of vs. One vs array for each shape element
        ns: This is an array of ns. One ns array for each shape element
        radius: one radius that is valid for all shape elements
        color: one vertex color that is valid for all shape elements

        See the same function in SimpleShape.
        """
        if props:
            if "vs" in props and props["vs"] is not None:
                vs = props["vs"]
            else:
                vs = [None for shape in self._shapes]
            if "ns" in props and props["ns"] is not None:
                ns = props["ns"]
            else:
                ns = [None for shape in self._shapes]
            if "radius" in props:
                radius = props["radius"]
            else:
                radius = None
            if "color" in props:
                color = props["color"]
            else:
                color = None
        assert len(vs) == len(self._shapes)
        assert len(ns) == len(self._shapes)
        for i, shape in enumerate(self._shapes):
            shape.vertex_props = {
                "vs": vs[i],
                "ns": ns[i],
                "radius": radius,
                "color": color,
            }
        self.merge_needed = True

    @property
    def edge_props(self):
        """Return a dictionary of the edge properties of the compound

        See setter what to expect.
        """
        d = self._shapes[0].edge_props
        return {
            "es": self.es,
            "radius": d["radius"],
            "color": d["color"],
            "draw_edges": d["draw_edges"],
        }

    @edge_props.setter
    def edge_props(self, props):
        """Set the edge properties for a whole compound shape at once

        Accepted is a dictionary with the following optional keys:
            es: This is an array of es. One es array for each shape element
            radius: one radius that is valid for all shape elements
            color: a list of colors (see SimpleShape.__init__). This list should contain an element
                for each shape.
            draw_edges: whether to draw the edges at all

        See the same function in SimpleShape.
        """
        if props:
            if "es" in props and props["es"] is not None:
                es = props["es"]
            else:
                es = [None for shape in self._shapes]
            if "radius" in props:
                radius = props["radius"]
            else:
                radius = None
            if "color" in props:
                color = props["color"]
            else:
                color = None
            if "draw_edges" in props:
                draw_edges = props["draw_edges"]
            else:
                draw_edges = None
        for i, shape in enumerate(self._shapes):
            shape.edge_props = {
                "es": es[i],
                "radius": radius,
                "color": color,
                "draw_edges": draw_edges,
            }
        self.merge_needed = True

    @property
    def face_props(self):
        """Return a dictionary of the face properties of the compound

        See face_props.setter what to expect.
        """
        d = self._shapes[0].face_props
        return {
            "fs": self.fs,
            "colors": self.shape_colors,
            "draw_faces": d["draw_faces"],
        }

    @face_props.setter
    def face_props(self, props):
        """Set the face properties for a whole compound shape at once

        Set to a dictionary with the following keys:
        fs: This is an array of es. One es array for each shape element
        colors: This is an array of colors. One colors set for each shape
                element.
        draw_faces: one draw_faces setting that is valid for all shape elements

        See the same function in SimpleShape.
        """
        if props:
            if "fs" in props and props["fs"] is not None:
                fs = props["fs"]
            else:
                fs = [None for shape in self._shapes]
            if "colors" in props and props["colors"] is not None:
                colors = props["colors"]
            else:
                colors = [None for shape in self._shapes]
            if "draw_faces" in props:
                draw_faces = props["draw_faces"]
            else:
                draw_faces = None
        for i, shape in enumerate(self._shapes):
            shape.face_props = {
                "fs": fs[i],
                "colors": colors[i],
                "draw_faces": draw_faces,
            }
        self.merge_needed = True

    def transform(self, trans):
        """Transform the model using the specified instance of a geomtypes.Trans3 object."""
        for shape in self._shapes:
            shape.transform(trans)
        self.merge_needed = True

    def scale(self, factor):
        """Scale the vertices of the object."""
        for shape in self._shapes:
            shape.scale(factor)
        self.merge_needed = True

    @property
    def dimension(self):
        """The shapes dimension, normally 3."""
        return self._shapes[0].dimension

    @property
    def vs(self):
        """Return an array of shape vertices."""
        return [shape.vs for shape in self._shapes]

    @property
    def ns(self):
        """Return an array of shape (vertex) normals."""
        return [shape.ns for shape in self._shapes]

    @property
    def es(self):
        """Return an array of shape edges."""
        return [shape.es for shape in self._shapes]

    @property
    def fs(self):
        """Return an array of shape faces."""
        return [shape.fs for shape in self._shapes]

    @property
    def shape_colors(self):
        """Get the color settings for all shapes."""
        return [shape.shape_colors for shape in self._shapes]

    @property
    def generate_normals(self):
        """Boolean stating whether vertex normals need to be (re)generated."""
        return self._shapes[0].generate_normals

    def to_off(
        self, precision=geomtypes.FLOAT_OUT_PRECISION, info=False, color_floats=False
    ):
        """Return a representation of the object in the 3D 'OFF' file format.

        See SimpleShape.to_off
        """
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.to_off(precision, info, color_floats)

    def to_postscript(
        self,
        face_indices=None,
        scaling=1,
        precision=7,
        page_size=PS.PageSizeA4,
    ):
        """Print in PS For each face where the other faces meet that face.

        Returns a string in PS format that shows the pieces of faces that can
        be used for constructing a physical model of the object.
        """
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.to_postscript(
            face_indices, scaling, precision, page_size
        )

    def get_dome(self, level=2):
        """Change the shape towards into a dome shaped model

        see SimpleShape.get_dome
        """
        if self.merge_needed:
            self.merge_shapes()
        return self.merged_shape.get_dome(level)


class SymmetricShape(CompoundShape):
    """
    The class describes simple shapes that have a base shape that is reused by
    some transformations. They can be expressed by a subset of all vertices,
    edges and faces. The isometries of the shape are then used to reproduce the
    complete shape.

    Colours can be specified for whole transformations of the base shape.
    """

    def __init__(
        self,
        vs,
        fs,
        es=None,
        ns=None,
        colors=None,
        isometries=None,
        regen_edges=True,
        orientation=None,
        name="SymmetricShape",
    ):
        """
        vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by gl_draw
        colors: optional array parameter describing the colours. Each element consists of RGB
            channel values (between 0 and 1). There should be an RGB value for each isometry..
        isometries: a list of all isometries that are needed to reproduce all
            parts of the shape can can be transformed from the specified base
            element through an isometry.
        regen_edges: if set to True then the shape will recreate the edges for all faces, i.e. all
            faces will be surrounded by edges. Edges will be filtered so that shared edges between
            faces, i.e. edges that have the same vertex index, only appear once. The creation of
            edges is not optimised and can take a long time.
        orientation: orientation of the base shape. This is an isometry operation.
        name: a string identifier representing the model.
        """
        # this is before creating the base shape, since it check "colors"
        self.base_shape = SimpleShape(
            vs,
            fs,
            es,
            ns=ns,
            colors=([colors[0]], []) if colors else None,
            orientation=orientation,
        )
        self.merged_shape = None
        if regen_edges:
            self.base_shape.regen_edges()
        super().__init__([self.base_shape], name=name)
        # This is save so heirs can still use repr_dict from this class
        self.json_class = SymmetricShape
        self.shape_colors = colors
        self.isometries = isometries if isometries else [E]
        self.order = len(isometries)
        self.needs_apply_isoms = True
        self.show_base_only = False

    def __repr__(self):
        # comment out class name, see comment at __fix_repr__ below:
        # s = indent.Str('%s(\n' % base.find_module_class_name(self.__class__, __name__))
        s = indent.Str("SymmetricShape(\n")
        s = s.add_incr_line("vs=[")
        s.incr()
        try:
            s = s.glue_line(
                ",\n".join(
                    indent.Str(repr(v)).reindent(s.indent) for v in self.base_shape.vs
                )
            )
        except AttributeError:
            logging.error("Are you sure the vertices are all of type geomtypes.Vec3?")
            raise
        s = s.add_decr_line("],")
        s = s.add_line("fs=[")
        s.incr()
        s = s.glue_line(
            ",\n".join(
                indent.Str(repr(f)).reindent(s.indent) for f in self.base_shape.fs
            )
        )
        s = s.add_decr_line("],")
        if self.base_shape.es != []:
            s = s.add_line(f"es={self.base_shape.es},")
        if self.base_shape.ns != []:
            s = s.add_incr_line("ns=[")
            s.incr()
            try:
                s = s.glue_line(
                    ",\n".join(repr(n).reindent(s.indent) for n in self.base_shape.ns)
                )
            except AttributeError:
                logging.error(
                    "Are you sure the normals are all of type geomtypes.Vec3?"
                )
                raise
            s = s.add_decr_line("],")
        s = s.add_line("colors=[")
        s.incr()
        cols = self._shape_colors
        s = s.glue_line(
            ",\n".join(indent.Str(repr(c)).reindent(s.indent) for c in cols)
        )
        s = s.add_decr_line("],")
        if self.isometries is not None:
            s = s.add_line("isometries=[")
            s.incr()
            s = s.glue_line(
                ",\n".join(
                    indent.Str(repr(i)).reindent(s.indent) for i in self.isometries
                )
            )
            s = s.add_decr_line("],")
        s = s.add_line(f"name='{self.name}',")
        s = s.glue_line(
            indent.Str(f"orientation={repr(self.base_shape.orientation)}").reindent(
                s.indent
            )
        )
        s = s.add_decr_line(")")
        if __name__ != "__main__":
            s = s.insert(f"{__name__}.")
        return s

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        # Note that orientation IS essential here.
        return {
            "class": base.class_to_json[self.json_class],
            "data": {
                "name": self.name,
                "vs": self.base_shape.vs,
                "fs": self.base_shape.fs,
                "cols": self._shape_colors,
                "orientation": self.base_shape.orientation.repr_dict,
                "isometries": [i.repr_dict for i in self.isometries],
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        # older version used a float between 0 and 1
        if isinstance(data["cols"][0], float):
            data["cols"] = [int(chn * 255) for chn in data["cols"]]
        o = data["orientation"]
        return cls(
            data["vs"],
            data["fs"],
            isometries=[
                base.json_to_class[s["class"]].from_json_dict(s)
                for s in data["isometries"]
            ],
            colors=data["cols"],
            orientation=base.json_to_class[o["class"]].from_json_dict(o),
            name=data["name"],
        )

    def merge_shapes(self):
        if self.show_base_only:
            # assuming that the base shape is a simple shape:
            self.merged_shape = self.base_shape
            self.merge_needed = False
        elif self.needs_apply_isoms:
            self.apply_isoms()

        super().merge_shapes()

    @staticmethod
    def _chk_face_colors_par(colors):
        """Check whether the colors parameters is valid.

        If not raise an assert.

        return the default colours (useful if default colors are used)
        """
        if not colors:
            colors = [rgb.gray95[:]]
        else:
            assert len(colors) > 0, "colors should have at least one element"
            col0 = colors[0]
            if isinstance(col0, (float, int)):
                # one colour specified for all
                assert (
                    len(colors) == 3 or len(colors) == 4
                ), f"Expected RGB(A), got {colors}"
                colors = [colors]
            else:
                # several colours specified
                assert isinstance(
                    col0, (list, tuple)
                ), f"expected first colour to be an RGB(A) value, got {col0}"
        return colors

    @property
    def shape_colors(self):
        """Get the color data for this shape (see colors @ __init__)."""
        return self._shape_colors

    @shape_colors.setter
    def shape_colors(self, colors):
        """Check and set the face colours and and save their properties."""
        colors = self._chk_face_colors_par(colors)
        self._shape_colors = colors
        self.merge_needed = True
        self.needs_apply_isoms = True

    def apply_colors(self):
        """
        Divide the shape colors over the isometries and re-assign class field.
        """
        no_of_cols = len(self._shape_colors)
        if no_of_cols != self.order:
            if no_of_cols == 1:
                col_data_per_shape = [self._shape_colors[0] for i in range(self.order)]
            elif no_of_cols < self.order:
                div = self.order // no_of_cols
                mod = self.order % no_of_cols
                col_data_per_shape = []
                for _ in range(div):
                    col_data_per_shape.extend(self._shape_colors)
                col_data_per_shape.extend(self._shape_colors[:mod])
            else:
                col_data_per_shape = (self._shape_colors[: self.order],)
            self._shape_colors = col_data_per_shape
            no_of_cols = len(self._shape_colors)
        # else: nothing to update
        assert no_of_cols == self.order, f"{no_of_cols} != {self.order}"

    def apply_isoms(self):
        """
        Apply the isometry operations for the current properties, like vs and
        colour settings.

        This will create all the individual shapes.
        """
        if len(self._shape_colors) != self.order:
            self.apply_colors()
        shapes = [
            SimpleShape(
                self.base_shape.vs,
                self.base_shape.fs,
                self.base_shape.es,
                ns=self.base_shape.ns,
                colors=([self._shape_colors[i]], []),
                orientation=isom * self.base_shape.orientation,
                name=f"{self.name}_{i}",
            )
            for i, isom in enumerate(self.isometries)
        ]
        self.set_shapes(shapes)
        self.needs_apply_isoms = False

    @property
    def base_vs(self):
        """Get the vertices of the base shape."""
        return self.base_shape.vs

    @base_vs.setter
    def base_vs(self, vs):
        """Set the vertices of the base shape.

        This will make sure that the necessary updates are made when needed.
        """
        assert len(vs) == len(self.base_shape.vs)
        self.base_shape.vertex_props = {"vs": vs}
        self.merge_needed = True
        self.needs_apply_isoms = True

    @property
    def orientation(self):
        """Get the base shape orientation."""
        return self.base_shape.orientation

    @orientation.setter
    def orientation(self, orientation):
        """Set the base shape orientation."""
        self.base_shape.orientation = orientation
        self.needs_apply_isoms = True

    @property
    def base_fs_props(self):
        """Get the face properties for the base_shape."""
        props = self.base_shape.face_props
        return {
            "fs": props["fs"],
            "colors": self._shape_colors[0],
            "draw_faces": self.props["draw_faces"],
        }

    @base_fs_props.setter
    def base_fs_props(self, props):
        """
        Define the properties of the faces for the base element.

        Accepted are the optional (keyword) parameters:
          - fs,
          - colors: see setter of shape_colors
          - colors: one RGB value (tuple / list) or a list of RGB values.
          - draw_faces: boolean stating whether to draw faces (default True)
        Check SimpleShape.face_props for more details.
        """
        if props:
            if "fs" in props and props["fs"] is not None:
                # The base shape must have some colour (which isn't really used
                base_shape_col = ([(241, 241, 241)], ())
                self.base_shape.face_props = {
                    "fs": props["fs"],
                    "colors": base_shape_col,
                }
                self.needs_apply_isoms = True
            if "colors" in props and props["colors"] is not None:
                self.shape_colors = props["colors"]
                self.merge_needed = True
            if "draw_faces" in props and props["draw_faces"] is not None:
                self.base_shape.draw_faces = props["draw_faces"]

    def transform(self, trans):
        """Transform the model using the specified instance of a geomtypes.Trans3 object."""

        def adjust_transform(isom):
            """Adjust the transform to global trans so the same result is obtained"""
            if isom.is_rot():
                return geomtypes.Rot3(angle=isom.angle(), axis=trans * isom.axis())
            if isom.is_rot_inv():
                return geomtypes.RotInv3(angle=isom.angle(), axis=trans * isom.axis())
            # reflection
            return geomtypes.Refl3(normal=trans * isom.plane_normal())

        self.isometries = [adjust_transform(isom) for isom in self.isometries]
        self.orientation = trans * self.orientation
        self.needs_apply_isoms = True

    def scale(self, factor):
        """Scale the vertices of the object."""
        self.base_shape.scale(factor)
        self.needs_apply_isoms = True

    def gl_draw(self):
        if self.show_base_only:
            self.base_shape.gl_draw()
        else:
            if self.needs_apply_isoms:
                self.apply_isoms()
            CompoundShape.gl_draw(self)

    def to_postscript(
        self,
        face_indices=None,
        scaling=1,
        precision=7,
        page_size=PS.PageSizeA4,
    ):
        """Print in PS For each face where the other faces meet that face.

        Returns a string in PS format that shows the pieces of faces that can
        be used for constructing a physical model of the object.
        """
        if self.merge_needed:
            self.merge_shapes()
        if not face_indices:
            # no need to print all faces in orbited, because of symmetry
            face_indices = list(range(len(self.base_shape.fs)))
        return self.simple_shape.to_postscript(
            face_indices, scaling, precision, page_size
        )


class SymmetricShapeSplitCols(SymmetricShape):
    """
    Same as a symmetric shape except that one can define a colour for each individual face.

    For this one shape_colors should be a color argument as in SimpleShape.__init__. which will be
    divided regularly over the symmetries. Optionally send in a list of these, where each element
    should be valid for each symmetry.
    """

    @staticmethod
    def _chk_face_colors_par(colors):
        """Check whether the colors parameters is valid.

        If not raise an assert.
        """
        if not colors:
            colors = [([rgb.gray95[:]], [])]
        assert len(colors) > 0, "colors should have at least one element"
        if isinstance(colors, tuple) or len(colors) == 2:
            colors = [colors]
        for c in colors:
            assert (
                len(c) == 2
            ), f"a colors element should be a 2-tuple (colors, face_i), got {c}"
        return colors

    def apply_isoms(self):
        """
        Apply the isometry operations for the current properties, like vs and
        colour settings.

        This will create all the individual shapes.
        """
        if len(self._shape_colors) != self.order:
            self.apply_colors()
        shapes = [
            SimpleShape(
                self.base_shape.vs,
                self.base_shape.fs,
                self.base_shape.es,
                ns=self.base_shape.ns,
                colors=self._shape_colors[i],
                orientation=isom * self.base_shape.orientation,
                name=f"{self.name}_{i}",
            )
            for i, isom in enumerate(self.isometries)
        ]
        self.set_shapes(shapes)
        self.needs_apply_isoms = False


class OrbitShape(SymmetricShape):
    """
    The class describes simple shapes that are symmetric. They can be expressed
    by a subset of all vertices, edges and faces. The symmetry of the shape is
    then used to reproduce the complete shape. To be able to know how to
    reproduce the shape one needs to know the symmetry of the complete shape and
    one needs to know which symmetry group the of the specified subset is. The
    later is called stabiliser in group algebra.
    From these two one can derive which isometries are needed to reproduce the
    complete shape.
    """

    def __init__(
        self,
        vs,
        fs,
        es=None,
        ns=None,
        final_sym=isometry.E,
        stab_sym=isometry.E,
        colors=None,
        regen_edges=True,
        name="OrbitShape",
        quiet=False,
    ):
        """
        vs: the vertices in the 3D object: an array of 3 dimension arrays, which
            are the coordinates of the vertices.
        fs: an array of faces. Each face is an array of vertex indices, in the
            order in which the vertices appear in the face.
        es: optional parameter edges. An array of edges. Each edges is 2
            dimensional array that contain the vertex indices of the edge.
        ns: optional array of normals (per vertex) This value might be [] in
            which case the normalised vertices are used. If the value is set it
            is used by gl_draw
        final_sym: the resulting symmetry of the shape.
        stab_sym: the symmetry of the stabiliser, which is a subgroup of final_sym
        colors: optional array parameter describing the colours. Each element consists of RGB
            channel values (between 0 and 1). There should be an RGB value for each isometry..
        regen_edges: if set to True then the shape will recreate the edges for all faces, i.e. all
            faces will be surrounded by edges. Edges will be filtered so that shared edges between
            faces, i.e. edges that have the same vertex index, only appear once. The creation of
            edges is not optimised and can take a long time.
        name: a string identifier representing the model.

        As an example: a square is used to define a cube. The square has a D4C4
        symmetry and the cube S4xI. The former is used as stab_sym and the latter
        as final_sym.
        The following parameters can be used:
        with v = lambda x, y, z: geomtypes.Vec3([x, y, z])
        vs = [v(1, 1, 1), v(1, -1, 1), v(1, -1, -1), v(1, 1, -1)] and
        fs = [[0, 1, 2, 3]]
        final_sym = S4xI(setup = {'o4axis0': v(0, 0, 1), 'o4axis1': v(0, 1, 0)})
        stab_sym = D4C4(setup = {'axis_n': v(1, 0, 0), 'normal_r': v(0, 1, 0)})
        colors: the colours per isometry. (use [] for none)
        """
        try:
            fs_quotient_set = final_sym / stab_sym
        except isometry.ImproperSubgroupError:
            logging.error("Stabiliser not a subgroup of final symmetry")
            raise
        len_f = len(final_sym)
        len_s = len(stab_sym)
        assert len_f % len_s == 0, f"Expected divisable group length {len_f} / {len_s}"
        fs_orbit = [coset.get_one() for coset in fs_quotient_set]
        if not quiet:
            logging.info("Applying an orbit of order %d", len(fs_orbit))
        super().__init__(
            vs, fs, es, ns, isometries=fs_orbit, name=name, regen_edges=regen_edges
        )
        # This is save so heirs can still use repr_dict from this class
        self.json_class = OrbitShape
        self.final_sym = final_sym
        self.stab_sym = stab_sym
        if colors != []:
            self.shape_colors = colors

    @property
    def repr_dict(self):
        """Return a short representation of the object."""
        return {
            "class": base.class_to_json[self.json_class],
            "data": {
                "name": self.name,
                "vs": self.base_shape.vs,
                "fs": self.base_shape.fs,
                "cols": self._shape_colors,
                "final_sym": self.final_sym.repr_dict,
                "stab_sym": self.stab_sym.repr_dict,
            },
        }

    @classmethod
    def from_dict_data(cls, data):
        # older version used a float between 0 and 1
        if isinstance(data["cols"][0][0], float):
            data["cols"] = [[int(chn * 255) for chn in d] for d in data["cols"]]
        return cls(
            data["vs"],
            data["fs"],
            final_sym=isometry.Set.from_json_dict(data["final_sym"]),
            stab_sym=isometry.Set.from_json_dict(data["stab_sym"]),
            colors=data["cols"],
            name=data["name"],
        )

    def __repr__(self):
        # This repr should be fixed, since you cannot be sure in which order the
        # isometry operation will be printed (there is no ordering in a Set.
        # This requires a more user friendly class interface for the user:
        # provide an array of colours and a symmetry (and index) on which the
        # colouring is based. For now fall back on the parental repr.
        s = indent.Str(f"{base.find_module_class_name(self.__class__, __name__)}(\n")
        s = s.add_incr_line("vs=[")
        s.incr()
        try:
            s = s.glue_line(
                ",\n".join(
                    indent.Str(repr(v)).reindent(s.indent) for v in self.base_shape.vs
                )
            )
        except AttributeError:
            logging.error("Are you sure the vertices are all of type geomtypes.Vec3?")
            raise
        s = s.add_decr_line("],")
        s = s.add_line("fs=[")
        s.incr()
        s = s.glue_line(
            ",\n".join(
                indent.Str(repr(f)).reindent(s.indent) for f in self.base_shape.fs
            )
        )
        s = s.add_decr_line("],")
        if self.base_shape.es != []:
            s = s.add_line(f"es={self.base_shape.es},")
        if self.base_shape.ns != []:
            s = s.add_incr_line("ns=[")
            s.incr()
            try:
                s = s.glue_line(
                    ",\n".join(repr(n).reindent(s.indent) for n in self.base_shape.ns)
                )
            except AttributeError:
                logging.error(
                    "Are you sure the normals are all of type geomtypes.Vec3?"
                )
                raise
            s = s.add_decr_line("],")
        s = s.add_line("colors=[")
        s.incr()
        cols = self._shape_colors
        s = s.glue_line(
            ",\n".join(indent.Str(repr(c)).reindent(s.indent) for c in cols)
        )
        s = s.add_decr_line("],")
        s = s.add_line("final_sym=")
        s.incr()
        s = s.glue_line((repr(self.final_sym) + ",").reindent(s.indent))
        s.decr()
        s = s.add_line("stab_sym=")
        s.incr()
        s = s.glue_line((repr(self.stab_sym) + ",").reindent(s.indent))
        s.decr()
        s = s.add_line(f"name='{self.name}',")
        s = s.add_decr_line(")")
        if __name__ != "__main__":
            s = s.insert(f"{__name__}.")
        return s

    def set_cols(self, colours, stab_sym):
        """
        Use the colours as specied and divide them according stab_sym

        colours: an array with rgb colour defs.
        stab_sym: the colours will be divided in a symmetric way, ie. in such a way that the base
            parts with the same colour have the symmetry stab_sym. For this to happen:
                1. the following is required:
                   - stab_sym is a subgroup of final_sym at object creation.
                2. the following is usually the case:

            An example of the usual case. A square is used to define a cube as explained in
            __init__. former is used as stab_sym at object creation and the latter as final_sym.
            CONTINUE here: testing cube example.., really need to read a Scene...
        """


class Scene(ABC):
    """
    Used for creating scenes in the PolyhedraBrowser.

    To implement a scene one typically needs to do the following:
    1. implement a class derived from geom_3d.SimpleShape
    2. implement a class derived from a wx.Frame window that controls the layout
       of a shape object from step 1.
    3. implement a scene class derived from this class as follows:
       class MyScene(geom_3d.Scene):
           def __init__(self, parent, canvas):
               geom_3d.Scene.__init__(self, MyShape, MyCtrlWin, parent, canvas)
       where MyShape is the class from step 1 and MyCtrlWin is the class from
       step 2.
    """

    def __init__(self, shape_class, ctrl_win_class, parent, canvas):
        """Create an object of the Scene class

        shape_class: a class derived from geom_3d.SimpleShape
        ctrl_win_class: a class derived from wx.Frame implementing controls to change the properties
            of the shape dynamically.
        parent: the main window of the application.
        canvas: the canvas on which the shape is supposed to be drawn with
                OpenGL.
        """
        self.shape = shape_class()
        self.ctrl_win = ctrl_win_class(self.shape, canvas, parent, wx.ID_ANY)

    def close(self):
        """Close the current scene and destroy all its widgets"""
        try:
            self.ctrl_win.Close(True)
        except RuntimeError:
            # The user probably closed the window already
            pass


# Classes that support conversion from and to JSON:
base.class_to_json[SimpleShape] = "shape"
base.class_to_json[CompoundShape] = "compound_shape"
base.class_to_json[SymmetricShape] = "symmetric_shape"
base.class_to_json[OrbitShape] = "orbit_shape"
base.json_to_class["shape"] = SimpleShape
base.json_to_class["compound_shape"] = CompoundShape
base.json_to_class["symmetric_shape"] = SymmetricShape
base.json_to_class["orbit_shape"] = OrbitShape
