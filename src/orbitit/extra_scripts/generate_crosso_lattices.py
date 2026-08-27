#!/usr/bin/env python3

import argparse
import math
import os
from pathlib import Path

from orbitit import geom_3d
from orbitit import geomtypes
import orbitit as orb

DESCR = """Generate crossohedra consisting of multiple crossohedra

E.g. a fractal of Siwissohedra.
"""

# global variables
V3 = math.sqrt(3)
OUT_DIR = "."
FLAT_TARTAN_CACHE = {}
TARTAN_3D_CACHE = {}

SWISS_W = 4  # width of standard Swissohedron
SWISS_HW = 2  # half width of standard Swissohedron
SWISS_R = 5 / 3
# must be set later
SWISSO = None
SWISS_VS = None
SWISS_F_PROPS = None
SWISS_FS = None
SWISS_COLS = None

DATA_DIR = (
    Path(os.path.dirname(os.path.realpath(__file__))) / ".." / "data" / "crossohedra"
)


def translate(vs, t):
    return [geomtypes.Vec3(v) + geomtypes.Vec3(t) for v in vs]


def rotate(vs, angle, axis):
    transform = geomtypes.Rot3(angle=angle, axis=geomtypes.Vec3(axis))
    return [transform * geomtypes.Vec3(v) for v in vs]


def get_flat_tartan(level):
    # Note: this is a recursive function. Normally it is a good idea to use globals instead of
    # parameters to save stack space, but for this function it doesn't make any sense to have more
    # than 4 recursion calls anyway.
    if level <= 1:
        return FLAT_TARTAN_CACHE[1]
    else:
        try:
            return FLAT_TARTAN_CACHE[level]
        except KeyError:
            pass
        base_shape, w = get_flat_tartan(level - 1)
        shape = geom_3d.CompoundShape([SWISSO])
        faces = base_shape.face_props
        vs = base_shape.vertex_props["vs"]
        for x in [-1, 1]:
            for y in [-1, 1]:
                f = w + SWISS_W
                arm_vs = translate(vs, [x * f, y * f, 0])
                arm = geom_3d.SimpleShape(
                    vs=arm_vs, fs=faces["fs"], colors=faces["colors"]
                )
                shape.add_shape(arm)
                octa_vs = translate(OCTA_VS, [x * SWISS_HW, y * SWISS_HW, 0])
                octa = geom_3d.SimpleShape(vs=octa_vs, fs=OCTA_FS, colors=OCTA_COLS)
                shape.add_shape(octa)
        shape = shape.simple_shape.clean_shape(10)
        FLAT_TARTAN_CACHE[level] = shape.filter_faces(keep_one=False), SWISS_W + 2 * w
        return FLAT_TARTAN_CACHE[level]


def get_3d_tartan(level):
    # Note: this is a recursive function. Normally it is a good idea to use globals instead of
    # parameters to save stack space, but for this function it doesn't make any sense to have more
    # than 4 recursion calls anyway.
    if level <= 1:
        return TARTAN_3D_CACHE[1]
    else:
        try:
            return TARTAN_3D_CACHE[level]
        except KeyError:
            pass
        base_shape, r = get_3d_tartan(level - 1)
        shape = geom_3d.CompoundShape([SWISSO])
        faces = base_shape.face_props
        vs = base_shape.vertex_props["vs"]
        lst = [-1, 1]
        # if level > 2:
        #    lst = [1]
        for x in lst:
            for y in lst:
                for z in lst:
                    if level == 2:
                        arm_vs = rotate(vs, math.pi, [x, y, z])
                    else:
                        arm_vs = vs
                    f = r + SWISS_R
                    arm_vs = translate(arm_vs, [x * f, y * f, z * f])
                    arm = geom_3d.SimpleShape(
                        vs=arm_vs, fs=faces["fs"], colors=faces["colors"]
                    )
                    shape.add_shape(arm)
        shape = shape.simple_shape.clean_shape(10)
        TARTAN_3D_CACHE[level] = shape.filter_faces(keep_one=False), SWISS_R + 2 * r
        return TARTAN_3D_CACHE[level]


def get_swisso_sponge_thinned(m):
    def get_list(c):
        result = []
        if c > -m:
            result.append(-1)
        if c < m:
            result.append(1)
        return result

    shape = geom_3d.CompoundShape([])
    for x in range(-m, m + 1):
        lx = get_list(x)
        for y in range(-m, m + 1):
            ly = get_list(y)
            for z in range(-m, m + 1):
                # for z in range(1, 3):
                lz = get_list(z)
                if z % 2 == 0:
                    even = x % 2 == 0 and y % 2 == 0 and (x + y) % 4 == 0
                    odd = (x % 2 == 1 or y % 2 == 1) and (x + y) % 2 == 0
                else:
                    even = x % 2 == 0 and y % 2 == 0 and (x + y) % 4 != 0
                    odd = False
                if even or odd:
                    # print(x, y, z)
                    vs = translate(SWISS_VS, [x * SWISS_W, y * SWISS_W, z * SWISS_W])
                    add_shape = geom_3d.SimpleShape(
                        vs=vs, fs=SWISS_FS, colors=SWISS_COLS
                    )
                    shape.add_shape(add_shape)
                if odd:
                    up_slope = (y - x) % 4 == 0
                    if up_slope:
                        if x > -m and y > -m:
                            octa_vs = translate(
                                OCTA_VS,
                                [
                                    x * SWISS_W - SWISS_HW,
                                    y * SWISS_W - SWISS_HW,
                                    z * SWISS_W,
                                ],
                            )
                            octa = geom_3d.SimpleShape(
                                vs=octa_vs, fs=OCTA_FS, colors=OCTA_COLS
                            )
                            shape.add_shape(octa)
                        if x < m and y < m:
                            octa_vs = translate(
                                OCTA_VS,
                                [
                                    x * SWISS_W + SWISS_HW,
                                    y * SWISS_W + SWISS_HW,
                                    z * SWISS_W,
                                ],
                            )
                            octa = geom_3d.SimpleShape(
                                vs=octa_vs, fs=OCTA_FS, colors=OCTA_COLS
                            )
                            shape.add_shape(octa)
                    else:
                        if x > -m and y < m:
                            octa_vs = translate(
                                OCTA_VS,
                                [
                                    x * SWISS_W - SWISS_HW,
                                    y * SWISS_W + SWISS_HW,
                                    z * SWISS_W,
                                ],
                            )
                            octa = geom_3d.SimpleShape(
                                vs=octa_vs, fs=OCTA_FS, colors=OCTA_COLS
                            )
                            shape.add_shape(octa)
                        if x < m and y > -m:
                            octa_vs = translate(
                                OCTA_VS,
                                [
                                    x * SWISS_W + SWISS_HW,
                                    y * SWISS_W - SWISS_HW,
                                    z * SWISS_W,
                                ],
                            )
                            octa = geom_3d.SimpleShape(
                                vs=octa_vs, fs=OCTA_FS, colors=OCTA_COLS
                            )
                            shape.add_shape(octa)
                elif z % 2 == 1 and even:
                    for sx in lx:
                        for sy in ly:
                            for sz in lz:
                                octa_vs = translate(
                                    OCTA_VS,
                                    [
                                        x * SWISS_W + sx * SWISS_HW,
                                        y * SWISS_W + sy * SWISS_HW,
                                        z * SWISS_W + sz * SWISS_HW,
                                    ],
                                )
                                octa = geom_3d.SimpleShape(
                                    vs=octa_vs, fs=OCTA_FS, colors=OCTA_COLS
                                )
                                shape.add_shape(octa)
    shape = shape.simple_shape.clean_shape(10)
    return shape.filter_faces(keep_one=False)


# TODO: use one generate function with argument
def generate_swisso_sponge_thinned(i_min, i_max):
    for i in range(i_min, i_max):
        result = get_swisso_sponge_thinned(i)
        filename = os.path.join(OUT_DIR, f"crosso_sponge_thinned_level{i}.off")
        with open(filename, "w") as fd:
            fd.write(result.to_off())
            print(f"written {filename}")


def generate_flat_tartan(i_min, i_max):
    for i in range(i_min, i_max):
        result, _ = get_flat_tartan(i)
        filename = os.path.join(OUT_DIR, f"crosso_fractal_flat_level{i}.off")
        with open(filename, "w") as fd:
            fd.write(result.to_off())
            print(f"written {filename}")


def generate_3d_tartan(i_min, i_max):
    """Generate a crossohedron in 3D tartan kind-a-version.

    i_min: generate from this level (including i_min)
    i_max: generate until this level (excluding i_max)
    """
    for i in range(i_min, i_max):
        result, _ = get_3d_tartan(i)
        filename = os.path.join(OUT_DIR, f"crosso_fractal_3d_level{i}.off")
        with open(filename, "w") as fd:
            fd.write(result.to_off())
            print(f"written {filename}")


def main():
    global DESCR, OUT_DIR, FLAT_TARTAN_CACHE, TARTAN_3D_CACHE
    global SWISSO, SWISS_VS, SWISS_F_PROPS, SWISS_FS, SWISS_COLS
    global OCTA, OCTA_VS, OCTA_F_PROPS, OCTA_FS, OCTA_COLS

    choice = {
        "tartan_flat": {"func": generate_flat_tartan},
        "tartan_3d": {"func": generate_3d_tartan},
        "sponge_swisso_thin": {"func": generate_swisso_sponge_thinned},
    }
    names = choice.keys()
    DESCR += "Valid names are: "
    DESCR += ", ".join(names)
    parser = argparse.ArgumentParser(description=DESCR)
    parser.add_argument(
        "-i",
        "--in-dir",
        type=str,
        default=DATA_DIR,
        help="Directory containing off files for base polyhedra",
    )
    parser.add_argument(
        "-l", "--level", type=int, default=1, help="The (lowest) level to develop"
    )
    parser.add_argument(
        "-n",
        "--no-of_levels",
        type=int,
        default=1,
        help="Number of levels to generate from the specified one",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        type=str,
        default=".",
        help="Directory to store the generated off files",
    )
    parser.add_argument("name", type=str, help="Name of crossohedron to develop")

    args = parser.parse_args()

    # TODO: add shape data in the script
    SWISSO = orb.read_shape_file(Path(args.in_dir) / "crosso-S4xI-o4_to_o3.off")
    SWISS_VS = SWISSO.vertex_props["vs"]
    SWISS_F_PROPS = SWISSO.face_props
    SWISS_FS = SWISS_F_PROPS["fs"]
    SWISS_COLS = SWISS_F_PROPS["colors"]

    # TODO: add shape data in the script
    OCTA = orb.read_shape_file(Path(args.in_dir) / "octahedron.off")
    OCTA_VS = OCTA.vertex_props["vs"]
    OCTA_F_PROPS = OCTA.face_props
    OCTA_FS = OCTA_F_PROPS["fs"]
    OCTA_COLS = OCTA_F_PROPS["colors"]

    FLAT_TARTAN_CACHE = {1: (SWISSO, 0)}

    TARTAN_3D_CACHE = {1: (SWISSO, SWISS_R)}

    OUT_DIR = args.out_dir
    choice[args.name]["func"](args.level, args.level + args.no_of_levels)


if __name__ == "__main__":
    main()
