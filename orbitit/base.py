#!/usr/bin/env python
"""Basic definitions for orbitit."""
from abc import ABC, abstractclassmethod, abstractproperty
import json

# Any class support from_json should update this: mapping a string to a class
json_to_class = {  # pylint: disable=C0103
}

# Any class support to_json should update this: mapping a class to a string representation
class_to_json = {  # pylint: disable=C0103
}

class Orbitit(ABC):
    """Shared base class for orbitit library."""
    json_indent = None

    @property
    def json_str(self):
        """Return a JSON representation of the object."""
        return json.dumps(self.repr_dict, sort_keys=True, indent=self.json_indent)

    def write_json_file(self, filename):
        """Write a JSON string representation to the specified path."""
        with open(filename, "w") as fd:
            fd.write(self.json_str)

    @abstractproperty
    def repr_dict(self):
        """Return a short representation of the object."""

    @classmethod
    def from_json_file(cls, filename):
        """Recreate object from JSON file."""
        with open(filename) as fd:
            s = fd.read()
        return cls.from_json_str(s)

    @classmethod
    def from_json_str(cls, json_str):
        """Recreate object from JSON string representation."""
        return cls.from_json_dict(json.loads(json_str))

    @classmethod
    def from_json_dict(cls, repr_dict):
        """Recreate object from complete dict representation."""
        cls_to_use = json_to_class[repr_dict["class"]]
        return cls_to_use.from_dict_data(repr_dict["data"])

    @abstractclassmethod
    def from_dict_data(cls, data):
        """Recreate object from the data field of the dict representation."""
        raise NotImplementedError


class Singleton(type):
    """Way of defining singleton classes."""
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def find_module_class_name(c, m):
    """ find the class from this module providing this function

        Used to prevent using class names from derived classes outside this
        module
        c: class
        m: module name

        return: the string representing the name of the class
    """
    def rec(c):
        """A recursive function that will return the class name."""
        if c.__module__ == m:
            return c.__name__
        for b in c.__bases__:
            n = rec(b)
            if n is not None:
                return n
        return None

    return rec(c)

def add_std_arguments_for_generating_models(parser, models_list, add_separate=True):
    """Add program arguments for generating standard polyhedra.

    parser: initialised argparser
    models_list: list of strings with models that are supported by the script.
    add_separate: set to True if models can be compound models
    """
    parser.add_argument(
        "--indent", "-i",
        metavar="NO-OF-SPACES",
        type=int,
        help="When using JSON format indent each line with the specified number of spaces to make "
        "it human readable. Note that the file size might increase significantly.",
    )
    parser.add_argument(
        "--models", "-m",
        metavar="NAME",
        nargs="*",
        help=f"Specifiy which model(s) to generate. Specify one of {models_list}. If nothing is "
        "specified all of them will be generated."
    )
    parser.add_argument(
        "--out-dir", "-o",
        default="",
        metavar="DIR",
        help="Specify possible output directory. Should exist.",
    )
    parser.add_argument(
        "--precision", "-p",
        metavar="NO-OF-DIGITS",
        type=int,
        help="Specify number of decimals to use when saving files. Negative numbers are ignored",
    )
    if add_separate:
        parser.add_argument(
            "--seperate-orbits", "-s",
            action='store_true',
            help="Also save the seperate parts consisting of one kind of polygon described by one "
            "orbit. This is always saved in JSON.",
        )
    parser.add_argument(
        "--json", "-j",
        action='store_true',
        help="Save the complete polyhedron in JSON format (default OFF)",
    )
