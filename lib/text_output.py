#!/usr/bin/python
#
# This file is part of lava-hacks.  lava-hacks is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Anders Roxell 2015

def get_sub_str(text, from_pos, num_chars, break_chars):
    sub_str = text[from_pos:from_pos+num_chars]
    for index, ch in enumerate(sub_str):
        if ch in break_chars:
            return (sub_str[:index], from_pos+index+1)
    return (sub_str, from_pos+len(sub_str))


class TextBlock(object):
    def __init__(self, text="", width=0):
        self.text = str(text)
        self.width = width
        self.block = list()


    def set_width(self, width, reflow=True):
        self.width = width

        if reflow: self.reflow()


    def set_text(self, text, reflow=True):
        self.text = str(text)

        if reflow: self.reflow()


    def append_text(self, new_text, reflow=True):
        self.text += str(text)

        if reflow: self.reflow()


    def get_block(self, start_line, num_lines):
        block_len = len(self.block)
        if start_line < 0:
            start_line = block_len-start_line-num_lines

        if start_line+num_lines > block_len:
            num_lines = block_len-start_line
        return self.block[start_line:start_line+num_lines]


    def reflow(self, width=0):
        if not self.width:
            raise Exception("Cannot reflow to windows of width %d" % self.width)

        del self.block[:]
        self.width = width or self.width

        text_len = len(self.text)
        cur_pos = 0

        while cur_pos < text_len:
            cur_line, next_pos = get_sub_str(self.text, cur_pos, self.width, ('\n',))
            self.block.append(cur_line)
            cur_pos = next_pos


# vim: set sw=4 sts=4 et fileencoding=utf-8 :
