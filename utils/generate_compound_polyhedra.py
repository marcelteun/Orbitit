#!/usr/bin/env python
"""
Generate off-files for compound polyhedra of polyhedra with tetrahedral symmetra.
"""

import argparse

from orbitit.compounds import generate
from orbitit import geom_3d


GENERATORS = {
    "S4A4": generate.CompoundS4A4,
    "S4xI": generate.CompoundS4xI,
}
final_sym = set({})
for generator in GENERATORS.values():
    final_sym |= generator.final_sym


parser = argparse.ArgumentParser(
    description="Generate off-files for compound polyhedra of polyhedra with tetrahedral "
    "symmetry. Will also create a JS script file for the interactive models"
)
parser.add_argument(
    "descriptive_sym",
    help=f"The symmetry of the descriptive. Supported are {list(GENERATORS.keys())}"
)
parser.add_argument(
    "-d",
    "--descriptive",
    help="The .off file for the descriptive, i.e. what you want to make a compound of. It "
    "should have the correct symmetry and it should be positioned in the standard way, "
    "I.e. for cube symmetry the 4-fold axes should be along the coordinate axes, and "
    "for tetrahedron and icosahedron symmetry the 2-fold axis should be along the z-axis. "
    "For all those symmetries, the 3-fold axis is along [1, 1, 1]. "
    "For the cyclic and the dihedral symmetries the n-fold axis is along the z-axis. "
    "Note that the script will not verify that this is the case. "
    "If not specified, then the cube is used. ",
)
parser.add_argument(
    "-n",
    nargs="+",
    type=int,
    default=[3],
    help="In case a dihedral or cyclic symmetry is specified, specify the order of the n-fold "
    "axis here.",
)
parser.add_argument(
    "-o",
    "--output-dir",
    default="",
    help="Output directory to store off-models in. The whole path will be created if "
    "it doesn't exist. By default output/<the argument descriptive_sym> is used",
)
parser.add_argument(
    "-f",
    "--final-symmetry",
    help="Specify this to only generate compounds having one symmetry group. "
    f"Must be one of {final_sym}.",
)
args = parser.parse_args()
final_symmetry = args.final_symmetry

try:
    generator = GENERATORS[args.descriptive_sym]
except KeyError as exception:
    err_msg = \
        f"Got invalid symmetry {args.descriptive_sym}, supported are {list(GENERATORS.keys())}"
    raise ValueError(err_msg) from exception
if final_symmetry and final_symmetry not in generator.final_sym:
    raise ValueError(
        f"Final symmetry {args.final_symmetry} not supported, only {generator.final_sym} "
        f"are supported for {args.descriptive_sym}"
    )

if not args.descriptive:
    DESCR = generator.example_descriptive
else:
    with open(args.descriptive) as fd:
        shape = geom_3d.read_off_file(fd)
        DESCR = {
            "vs": shape.vs,
            "fs": shape.fs,
        }

output_dir = args.output_dir
if not output_dir:
    output_dir = f"output/{args.args.descriptive_sym}"

compounds = generator(DESCR, output_dir, args.final_symmetry, n=args.n)