#!/usr/bin/env python
"""Test module for orbitit.indent.py"""
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
import unittest

from orbitit import indent

EXPECTED = """for one in all {
    do something
    do some more
        new_block
        blabla
                further
                bis
        grr
        arg
    back
    same
} done
"""

class TestStr(unittest.TestCase):
    """Unit tests for ident.Str"""

    def test_indent(self):
        """Test increase and decrease of some text"""
        text = indent.Str("")
        text = text.add_line("for one in all {")
        text.incr()
        text = text.add_line("do something")
        text = text.add_line("do some more")
        text = text.add_incr_line("new_block")
        text = text.add_line("blabla")
        text = text.add_incr_line("further", 2)
        text = text.add_line("bis")
        text = text.add_decr_line("grr", 2)
        text = text.add_line("arg")
        text = text.add_decr_line("back")
        text = text.add_line("same")
        text.decr()
        text = text.add_line("} done")
        self.assertEqual(text, EXPECTED, "Test case test_indent failed")


if __name__ == '__main__':
    unittest.main()
