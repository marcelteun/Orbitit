#!/usr/bin/python
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
#------------------------------------------------------------------

class Str(str):
    def __new__(this, s = '', indent_step = 4, indent = 0):
        return str.__new__(this, s)

    def __init__(this, s = '', indent_step = 4, indent = 0):
        this.indent_step = indent_step
        this.indent = indent
        if this.indent < 0:
            this.indent = 0

    def _chk_indent(this):
        if this.indent < 0:
            this.indent = 0

    def cp_props(this, s):
        s.indent = this.indent
        s.indent_step = this.indent_step

    def glue_line(this, s):
        """add a line that already has indentation, i.e. don't indent"""
        return Str(
            "%s%s\n" % (this, s),
            this.indent_step,
            this.indent
        )

    def add_line(this, s):
        return Str(
            "%s%s%s\n" % (this, ' ' * this.indent, s),
            this.indent_step,
            this.indent
        )

    def add_incr_line(this, s, i = 1):
        this.incr(i)
        return this.add_line(s)

    def add_decr_line(this, s, i = 1):
        this.decr(i)
        return this.add_line(s)

    def incr(this, i = 1):
        this.indent = this.indent + i * this.indent_step

    def decr(this, i = 1):
        this.indent = this.indent - i * this.indent_step
        if this.indent < 0:
            this.indent = 0

    def insert(this, s):
        return Str(
            "%s%s" % (s, this),
            this.indent_step,
            this.indent
        )

    def reindent(this, i):
        """Indent the the whole block with i indent steps.

        Currently only i >= 0 is supported
        Note: newlines will not get an indentation.
        """
        return Str('\n'.join(
                s if s == '' else (i * ' ') + s for s in this.splitlines()
            )
        )


if __name__ == '__main__':
    c = """for one in all {
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
    s = Str()
    s = s.add_line('for one in all {')
    s.incr()
    s = s.add_line('do something')
    s = s.add_line('do some more')
    s = s.add_incr_line('new_block')
    s = s.add_line('blabla')
    s = s.add_incr_line('further', 2)
    s = s.add_line('bis')
    s = s.add_decr_line('grr', 2)
    s = s.add_line('arg')
    s = s.add_decr_line('back')
    s = s.add_line('same')
    s.decr()
    s = s.add_line('} done')
    assert(c == s), 'test failed:\n>%s< != >%s<' % (c, s)

    print('test passed')
