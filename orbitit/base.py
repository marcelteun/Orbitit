#!/usr/bin/env python
"""Basic definitions for orbitit."""
from abc import ABC, abstractclassmethod, abstractproperty
import json

# Any class support from_json should update this: mapping a string to a class
json_to_class = {
}

# Any class support to_json should update this: mapping a class to a string representation
class_to_json = {
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
        else:
            for b in c.__bases__:
                n = rec(b)
                if n != None:
                    return n
        return None

    return rec(c)
