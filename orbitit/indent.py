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
    def __new__(cls, s, *_, **__):
        return super().__new__(cls, s)

    def __init__(self, _, indent_step=4, indent=0):
        super().__init__()
        assert indent_step >= 0, f"indent_step must be bigger than 0, got {indent_step}"
        self.indent_step = indent_step
        self.indent = max(indent, 0)

    def glue_line(self, s):
        """Add a line that already has indentation, i.e. don't indent.

        s: the text string to be added. A new line is added at the end of the provided text.
        """
        return Str(f"{self}{s}\n", self.indent_step, self.indent)

    def add_line(self, s):
        """Add a line with the current indentation.

        s: the text string to be indented and added. A new line is added at the end of the provided
            text.
        """
        return Str(f"{self}{' ' * self.indent}{s}\n", self.indent_step, self.indent)

    def add_incr_line(self, s, i=1):
        """Add a line with an increased indentation.

        s: the text string to be indented and added. A new line is added at the end of the provided
            text.
        i: express with how many steps the indentation needs to be increased. Default 1.
        """
        self.incr(i)
        return self.add_line(s)

    def add_decr_line(self, s, i=1):
        """Add a line with an decreased indentation.

        s: the text string to be indented and added. A new line is added at the end of the provided
            text.
        i: express with how many steps the indentation needs to be decreased. Default 1.
        """
        self.decr(i)
        return self.add_line(s)

    def incr(self, i=1):
        """
        Increase the indentation with the specified amount of steps

        i: express with how many steps the indentation needs to be increased. Default 1.
        """
        self.indent = self.indent + i * self.indent_step

    def decr(self, i=1):
        """
        Decrease the indentation with the specified amount of steps

        i: express with how many steps the indentation needs to be decreased. Default 1.
        """
        self.indent = max(self.indent - i * self.indent_step, 0)

    def insert(self, s):
        """Prepend the current text with the specified text (no indentation is added)"""
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
