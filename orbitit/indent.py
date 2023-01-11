#!/usr/bin/env python
"""File for handling creating text with indentation."""
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


class Str(str):
    """A string type that handles increase and decrease of indentation."""
    def __new__(cls, s="", indent_step=4, indent=0):
        return str.__new__(cls, s)

    def __init__(self, s="", indent_step=4, indent=0):
        self.indent_step = indent_step
        self.indent = indent
        if self.indent < 0:
            self.indent = 0

    def _chk_indent(self):
        if self.indent < 0:
            self.indent = 0

    def cp_props(self, s):
        s.indent = self.indent
        s.indent_step = self.indent_step

    def glue_line(self, s):
        """add a line that already has indentation, i.e. don't indent"""
        return Str(f"{self}{s}\n", self.indent_step, self.indent)

    def add_line(self, s):
        return Str(f"{self}{' ' * self.indent}{s}\n", self.indent_step, self.indent)

    def add_incr_line(self, s, i=1):
        self.incr(i)
        return self.add_line(s)

    def add_decr_line(self, s, i=1):
        self.decr(i)
        return self.add_line(s)

    def incr(self, i=1):
        self.indent = self.indent + i * self.indent_step

    def decr(self, i=1):
        self.indent = self.indent - i * self.indent_step
        if self.indent < 0:
            self.indent = 0

    def insert(self, s):
        return Str(f"{s}{self}", self.indent_step, self.indent)

    def __add__(self, s):
        return Str(f"{self}{s}", self.indent_step, self.indent)

    def reindent(self, i):
        """Indent the the whole block with i indent steps.

        Currently only i >= 0 is supported
        Note: newlines will not get an indentation.
        """
        return Str(
            "\n".join(s if s == "" else (i * " ") + s for s in self.splitlines())
        )
