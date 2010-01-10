#!/usr/bin/python
"""
A header with blocks of 4 bytes.

The first one is incremented from 0x04 to 0xC4, by steps of 0x20.
The second byte looks like a count for each set of 8 * 4 bytes, starting
at 0x03.
The third and fourth are probably an uint16, represnenting the width of the
character.

"""

# import Image and the graphics package Tkinter
import Image
import struct
import sys

class Glyph:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.pixels = None
        self.raw = [ ]
        self.color = 0xFF

    def get_image(self, color=0xFF):
        if self.pixels is None:
            self.load_pixels()

        val_true = chr(color)
        val_false = chr(0)
        data = "".join([x and val_true or val_false for x in self.pixels])
        return Image.fromstring("L", (self.width, self.height), data,
                                "raw", "L", 16, 1)

    def clear(self):
        self.pixels  = [ 0 ] * 255

    def load_pixels(self):
        pixels = [ ]
        for ch in self.raw:
            pixels += [((ch >> i) & 1) for i in range(15, -1, -1)]
        self.pixels = pixels


class Font:
    def __init__(self, filename=None):
        self.max_width = 0
        self.max_height = 0
        self.letter_spacing = 1
        self.glyphs = [ ]
        self.filename = filename

        if filename is not None:
            self.load(filename)

    def add_space_glyph(self):
        """Since space is not included, add it as the first glyph."""
        space = Glyph()
        space.width = self.max_width - 1
        space.height = self.max_height
        space.clear()
        self.glyphs.append(space)

    def load(self, filename):
        self.filename = filename

        fp = open(filename, "rb")
        data = fp.read()
        fp.close()

        self.max_width, self.max_height = struct.unpack_from("<HH", data)

        self.add_space_glyph()

        for i in range(1, 241):
            offset = struct.unpack_from("<H", data, i * 4)[0]
            width = struct.unpack_from("<H", data, i * 4 + 2)[0]

            if width == 0:
                continue

            glyph = Glyph()
            glyph.width = width
            glyph.height = self.max_height
            glyph.raw = struct.unpack_from("<" + "H" * 16, data, offset)
            self.glyphs.append(glyph)

    def get_glyph_for(self, ch):
        """Glyphs are in ASCII order, starting at 32."""
        idx = ord(ch) - 32
        return self.glyphs[idx]

    def calculate_width(self, value):
        """Given a string, return the width in pixels to fit it."""
        width = 0

        for ch in value:
            glyph = self.get_glyph_for(ch)
            width += glyph.width + self.letter_spacing
        
        return width

    def get_map(self, value=None):
        """Return a large image with all the glyphs."""

        if value is None:
            width = self.max_width * len(self.glyphs)
            height = self.max_height
            buf = "\0" * (width * height)
            im = Image.fromstring("L", (width, height), buf, "raw", "L", 0, 1)
            for i, glyph in enumerate(self.glyphs):
                im.paste(glyph.get_image(), (i * self.max_width, 0))
        else:
            im = self.draw_line(value)

        return im

    def draw_line(self, value, leftmargin=0, color=0xFF):
        if value == "":
            return None

        width = self.calculate_width(value) + leftmargin
        height = self.max_height
        buf = "\x00" * (width * height)
        im = Image.fromstring("L", (width, height), buf, "raw", "L", 1, 1)
        cursor = leftmargin

        for ch in value:
            glyph = self.get_glyph_for(ch)
            im.paste(glyph.get_image(color), (cursor, 0))
            cursor += glyph.width + self.letter_spacing

        return im
