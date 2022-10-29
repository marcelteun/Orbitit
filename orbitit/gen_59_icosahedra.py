#!/usr/bin/env python3
"""The script can be used to generate the 59 stellations of the icosahedron as enumarised by
Coxeter.
"""
# all vertices of the stellation template
from math import sqrt
import os

from orbitit.orbit import Shape
from orbitit.geomtypes import Vec3
from orbitit.isometry import A5, A5xI, C3, E

V5 = sqrt(5)
V3 = sqrt(3)
TAU = (1 + V5) / 2
TAU_2 = (3 + V5) / 2  # TAU**2
TAU_3 = 2 + V5  # TAU**3
TAU_4 = (7 + 3 * V5) / 2  # TAU**4
TAU_4_SUB_1 = TAU_4 - 1
D_TAU = (V5 - 1) / 2  # 1 / TAU
HEIGHT = TAU_2 / V3

VS = [
    # the base triangle
    Vec3([1, 1 / V3, HEIGHT]),  # 0
    Vec3([-1, 1 / V3, HEIGHT]),  # 1
    Vec3([0, -2 / V3, HEIGHT]),  # 2
    # the big triangle from the great icosahedron
    Vec3([-TAU_4, -TAU_4 / V3, HEIGHT]),  # 3
    Vec3([TAU_4, -TAU_4 / V3, HEIGHT]),  # 4
    Vec3([0, 2 * TAU_4 / V3, HEIGHT]),  # 5
    # The extra points on the edges of the big triangle
    Vec3([-TAU, -TAU_4 / V3, HEIGHT]),  # 6
    Vec3([TAU, -TAU_4 / V3, HEIGHT]),  # 7
    Vec3([TAU_3, 1 / V3, HEIGHT]),  # 8
    Vec3([TAU_2, TAU_4_SUB_1 / V3, HEIGHT]),  # 9
    Vec3([-TAU_2, TAU_4_SUB_1 / V3, HEIGHT]),  # 10
    Vec3([-TAU_3, 1 / V3, HEIGHT]),  # 11
    # The vertices of the first stellation layer
    Vec3([0, 2 * TAU_4_SUB_1 / 5 / V3, HEIGHT]),  # 12
    Vec3([-TAU_4_SUB_1 / 5, -TAU_4_SUB_1 / 5 / V3, HEIGHT]),  # 13
    Vec3([TAU_4_SUB_1 / 5, -TAU_4_SUB_1 / 5 / V3, HEIGHT]),  # 14
    # second stellation layer
    Vec3([-TAU / 2, TAU_4 / 2 / V3, HEIGHT]),  # 15
    Vec3([-TAU_2 / 2, -TAU_4_SUB_1 / 2 / V3, HEIGHT]),  # 16
    Vec3([(2 + V5) / 2, -V3 / 6, HEIGHT]),  # 17
    Vec3([TAU / 2, TAU_4 / 2 / V3, HEIGHT]),  # 18
    Vec3([-(2 + V5) / 2, -V3 / 6, HEIGHT]),  # 19
    Vec3([TAU_2 / 2, -TAU_4_SUB_1 / 2 / V3, HEIGHT]),  # 20
    # third stellation layer, first kind
    Vec3([0, 4 / V3, HEIGHT]),  # 21
    Vec3([-2, -2 / V3, HEIGHT]),  # 22
    Vec3([2, -2 / V3, HEIGHT]),  # 23
    # third stellation layer, second kind
    Vec3([TAU, (3 * V5 - 1) / 2 / V3, HEIGHT]),  # 24
    Vec3([-TAU, (3 * V5 - 1) / 2 / V3, HEIGHT]),  # 25
    Vec3([-V5, 1 / V3, HEIGHT]),  # 26
    Vec3([-D_TAU, -(3 * V5 + 1) / 2 / V3, HEIGHT]),  # 27
    Vec3([D_TAU, -(3 * V5 + 1) / 2 / V3, HEIGHT]),  # 28
    Vec3([V5, 1 / V3, HEIGHT]),  # 29
    # fourth stellation layer, first kind
    Vec3([0, -(6 * V5 + 10) / 5 / V3, HEIGHT]),  # 30
    Vec3([(6 * V5 + 10) / 10, (6 * V5 + 10) / 10 / V3, HEIGHT]),  # 31
    Vec3([-(6 * V5 + 10) / 10, (6 * V5 + 10) / 10 / V3, HEIGHT]),  # 32
    # fourth stellation layer, second kind
    Vec3([(V5 + 5) / 10, (25 + 9 * V5) / 10 / V3, HEIGHT]),  # 33
    Vec3([-TAU_2, -(5 + 3 * V5) / 10 / V3, HEIGHT]),  # 34
    Vec3([(5 + 2 * V5) / 5, -(10 + 3 * V5) / 5 / V3, HEIGHT]),  # 35
    Vec3([-(V5 + 5) / 10, (25 + 9 * V5) / 10 / V3, HEIGHT]),  # 36
    Vec3([-(5 + 2 * V5) / 5, -(10 + 3 * V5) / 5 / V3, HEIGHT]),  # 37
    Vec3([TAU_2, -(5 + 3 * V5) / 10 / V3, HEIGHT]),  # 38
    # final stellation, first kind
    Vec3([0, -(6 * V5 + 14) / V3, HEIGHT]),  # 39
    Vec3([(6 * V5 + 14) / 2, (6 * V5 + 14) / 2 / V3, HEIGHT]),  # 40
    Vec3([-(6 * V5 + 14) / 2, (6 * V5 + 14) / 2 / V3, HEIGHT]),  # 41
    # final stellation, second kind
    Vec3([TAU_3, (6 * V5 + 13) / V3, HEIGHT]),  # 42
    Vec3([-TAU_3, (6 * V5 + 13) / V3, HEIGHT]),  # 43
    Vec3([-(7 * V5 + 15) / 2, -TAU_4 / V3, HEIGHT]),  # 44
    Vec3([-(5 * V5 + 11) / 2, -(9 * V5 + 19) / 2 / V3, HEIGHT]),  # 45
    Vec3([(5 * V5 + 11) / 2, -(9 * V5 + 19) / 2 / V3, HEIGHT]),  # 46
    Vec3([(7 * V5 + 15) / 2, -TAU_4 / V3, HEIGHT]),  # 47
]
# Actually A5xI should always be used, but A5 is an optimisation
FINAL_SYM = [
    A5(setup={"o3axis": Vec3([0, 0, 1]), "o5axis": Vec3(VS[2])}),
    A5xI(setup={"o3axis": Vec3([0, 0, 1]), "o5axis": Vec3(VS[2])}),
]
STAB_SYM = [
    C3(setup={"axis": Vec3([0, 0, 1])}),
    E(),
]
STELLATIONS = [
    {
        "id": "A",
        "Vs": [VS[i] for i in [0, 1, 2]],
        "Fs": [[0, 1, 2]],
        "final": 0,
        "stab": 0,
        "col_alt": 0,
    },
    {
        "id": "B",
        "Vs": [VS[i] for i in [0, 12, 1, 13, 2, 14]],
        "Fs": [[0, 1, 2, 3, 4, 5]],
        "final": 0,
        "stab": 0,
        "col_alt": 0,
    },
    {
        "id": "C",
        "Vs": [VS[i] for i in [15, 16, 17, 18, 19, 20]],
        "Fs": [[0, 1, 2], [3, 4, 5]],
        "final": 0,
        "stab": 0,
        "col_alt": 0,
    },
    {
        "id": "D",
        "Vs": [VS[i] for i in [1, 15, 25, 12, 18, 21, 0, 24]],
        "Fs": [[0, 1, 2], [1, 3, 4, 5], [4, 6, 7]],
        "final": 0,
        "stab": 1,
        "col_alt": 2,
    },
    {
        "id": "E",
        "Vs": [VS[i] for i in [33, 21, 18, 24, 9, 0, 29, 31, 17, 8, 23, 38]],
        "Fs": [[0, 1, 2], [2, 3, 4], [3, 5, 6, 7], [6, 8, 9], [8, 10, 11]],
        "final": 0,
        "stab": 1,
        "col_alt": 2,
    },
    {
        "id": "F",
        "Vs": [VS[i] for i in range(0, 12)],
        "Fs": [[0, 2, 4], [1, 0, 5], [2, 1, 3], [6, 8, 10], [7, 9, 11]],
        "final": 0,
        "stab": 0,
        "col_alt": 0,
    },
    {
        "id": "G",
        "Vs": [VS[i] for i in [3, 4, 5]],
        "Fs": [[0, 1, 2]],
        "final": 0,
        "stab": 0,
        "col_alt": 0,
    },
    {
        "id": "H",
        "Vs": [VS[i] for i in [6, 39, 7, 46, 4, 47, 8]],
        "Fs": [[0, 1, 2], [2, 3, 4], [4, 5, 6]],
        "final": 0,
        "stab": 1,
        "col_alt": 3,
    },
    {
        "id": "e1",
        "Vs": [VS[i] for i in [18, 24, 9, 15, 10, 25, 12, 21]],
        "Fs": [[0, 1, 2], [3, 4, 5], [0, 7, 3, 6]],
        "final": 0,
        "stab": 1,
        "col_alt": 2,
    },
    {
        "id": "f1",
        "Vs": [VS[i] for i in [32, 25, 10, 15, 36, 21]],
        "Fs": [[0, 1, 2], [1, 2, 3], [2, 3, 4], [4, 3, 5]],
        "final": 1,
        "stab": 1,
        "col_alt": 4,
    },
    {
        "id": "g1",
        "Vs": [VS[i] for i in [36, 15, 10, 11, 32, 34, 19]],
        "Fs": [[0, 1, 2], [2, 3, 4], [3, 5, 6]],
        "final": 0,
        "stab": 1,
        "col_alt": 2,
    },
    {
        "id": "e1f1",
        "Vs": [VS[i] for i in [32, 25, 10, 15, 36, 21, 33, 18, 12, 9, 24, 31]],
        "Fs": [[0, 1, 2], [2, 3, 4], [3, 4, 5, 6, 7, 8], [6, 7, 9], [9, 10, 11]],
        "final": 0,
        "stab": 1,
        "col_alt": 2,
    },
]

if __name__ == "__main__":
    import argparse

    def generate_models():
        """Generate models for the stellations."""
        for no, data in enumerate(STELLATIONS):
            model = Shape(
                data,
                final_sym=FINAL_SYM[data["final"]],
                stab_sym=STAB_SYM[data["stab"]],
                name=f"Stellation of Icosahedron no. {no}: {data['id']}",
                no_of_cols=5,
                col_alt=data["col_alt"],
            )
            filename = os.path.join( ARGS.output_dir, f"icosahedron{no}_{data['id']}.json")
            model.write_json_file(filename)
            print("written", filename)

    PARSER = argparse.ArgumentParser(description="Generate the stellation of the icosahedron")
    PARSER.add_argument(
        "--output-dir",
        "-o",
        default=".",
        metavar="path",
        help="The output directory to store the stellation files",
    )
    ARGS = PARSER.parse_args()
    if not os.path.isdir(ARGS.output_dir):
        os.mkdir(ARGS.output_dir)
    generate_models()

# vim expandtab sw=4
