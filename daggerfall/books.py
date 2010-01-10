#!/usr/bin/env python3
"""
This is an attempt at creating a Daggerfall book reader. Here is the spec used
to read them. It is inspired from experiments and from the documentation
available on uesp.net:

  00 - 3F    char[64]         Book Title (NUL padded)
  40 - 7F    char[64]         Author (NUL padded)
  80 - DF    4 * char[64]     Topics 1 to 4 (incl. naughty flag)
  E0 - E3    uint32 (LE)      Price
  E4 - E5    uint16 (LE)      Unknown1, category? values: 1, 2, 3, 4
  E6 - E7    uint16 (LE)      Unknown2, 12345 or 12346
  E8 - E9    uint16 (LE)      Unknown3, 23456 or 23457
  EA - EB    uint16 (LE)      Book Page Count
  EC - xx    y * uint32 (LE)  Page Offsets
                              y is the PageCount, xx = 0xEC + y * 4

"""

import sys
import struct
import daggerfall
from fonts import Font

fonts = { }

def get_font(typeid):
    global fonts

    if typeid in fonts:
        return fonts[typeid]

    if typeid is 0:
        typeid = 4

    filename = daggerfall.get_abspath("FONT%04d.FNT" % (typeid - 1))
    font = Font(filename)
    fonts[typeid] = font
    return font

class Line():
    def __init__(self, page):
        self.page = page
        self.align = "LEFT"
        self.value = ""
        self.position_x = 0
        self.position_y = 0
        self.set_fontid(0)

    def set_fontid(self, font_id):
        self.font_id = font_id
        self.font = get_font(font_id)

    def get_pos(self):
        return [ self.position_x, self.position_y ]

    def get_image(self, color=0xFF):
        width = self.font.calculate_width(self.value)
        if self.align == "CENTER":
            leftmargin = int((self.page.width - width) / 2) - 9
        else:
            leftmargin = 0
        return self.font.draw_line(self.value, leftmargin=leftmargin, color=color)
    

class Page():
    def __init__(self, raw=None):
        self.raw = raw
        self.lines = [ ]
        self.cursor_y = 0
        self.width = 320
        self.height = 200
        if raw is not None:
            self.raw = [ord(ch) for ch in raw]
            self.extract_lines()

    def add_header(self, value):
        line = Line(self)
        line.value = value
        line.set_fontid(2)
        line.align = "CENTER"
        line.position_y = self.cursor_y
        self.lines.append(line)
        self.cursor_y += line.font.max_height

    def add_line(self, value):
        line = Line(self)
        line.value = value
        line.position_y = self.cursor_y
        self.lines.append(line)
        self.cursor_y += line.font.max_height

    def add_lines(self, values):
        splits = values.split("\n")
        for split in splits:
            self.add_line(split)

    def extract_lines(self):
        line = Line(self)
        skip = 0

        def next(self, line):
            line.position_y = self.cursor_y
            self.cursor_y += line.font.max_height
            self.lines.append(line)
            new_line = Line(self)
            new_line.set_fontid(line.font_id)
            return new_line

        for i, c in enumerate(self.raw):
            if skip > 0:
                skip -= 1
                continue
            
            if c >= 0x20 and c <= 0x7F:
                line.value += chr(c)
            # NewLineOffset
            elif c == 0x00:
                line = next(self, line)
                if self.raw[i+1] == 0xFB:
                    skip += 3
                    line.position_x = self.raw[i+2]
                    line.position_y = self.raw[i+3]
                continue
            # SameLineOffset
            elif c == 0x01:
                if self.raw[i+1] == 0xFB:
                    skip += 3
                    line.position_x = self.raw[i+2]
                    line.position_y = self.raw[i+3]
                continue
            elif c == 0xFC:
                line.align = "JUSTIFY"
                if self.raw[i+1] == 0x00:
                    skip += 1
                    line = next(self, line)
            elif c == 0xFD:
                line.align = "CENTER"
                if self.raw[i+1] == 0x00:
                    skip += 1
                    line = next(self, line)
            elif c == 0xF9:
                # The next byte is the font style (0-3)
                line.set_fontid(self.raw[i+1])
                skip += 1
            elif c == 0xF6:
                break
            else:
                raise Exception("Unknown token: 0x%02X at 0x%04X" % (c, i))
        self.lines.append(line)

    def create_markup(self, buf):
        markup = "<Page RawSize=\"%d\">" % len(buf)
        skip = 0
        for i, c in enumerate(buf):
            if skip > 0:
                skip -= 1
                continue

            if c >= 0x20 and c <= 0x7F:
                markup += chr(c)
            elif c == 0x00:
                markup += "<NOP />"
            elif c == 0xFC:
                markup += "<StartJustify />"
                if buf[i+1] == 0x00:
                    skip += 1
                    markup += "<EndOfLine />\n"
            elif c == 0xFD:
                markup += "<CenterPreceeding />"
                if buf[i+1] == 0x00:
                    skip += 1
                    markup += "<EndOfLine />\n"
            elif c == 0xF9:
                font_type = buf[i+1]
                markup += "<Font Style=\"%d\">" % font_type
                skip += 1
            elif c == 0xF6:
                markup += "<EndOfPage />"
                break
            else:
                markup += "<UNKNOWN: %02X>" % c
        markup += "</Page>"

        return markup


class Book():
    def __init__(self, filename=None):
        self.title = None
        self.author = None
        self.topics = [ ]
        self.is_naughty = False
        self.price = -1
        self.filename = filename

        self.unknown1 = -1
        self.unknown2 = -1
        self.unknown3 = -1

        self.page_count = 0
        self.page_offsets = [ ]
        self.pages = [ ]

        if filename is not None:
            self.open(filename)

    def add_topic(self, name):
        if len(name) > 0:
            self.topics.append(name)

    def open(self, filename):
        try:
            fp = open(filename, "rb")
            buf = fp.read()
            fp.close()
        except:
            print("Unable to open %s" % filename)
            sys.exit(-1)

        self.filename = filename
        buflen = len(buf)

        self.title =   str(buf[0x0000:0x003F].strip("\0"))
        self.author =  str(buf[0x0040:0x007F].strip("\0"))
        self.add_topic(str(buf[0x0080:0x0097].strip("\0")))
        self.add_topic(str(buf[0x0098:0x00AF].strip("\0")))
        self.add_topic(str(buf[0x00B0:0x00C6].strip("\0")))
        self.add_topic(str(buf[0x00C7:0x00DF].strip("\0")))

        if "naughty" in self.topics:
            self.is_naughty = True

        self.price = struct.unpack_from("<I", buf, 0x00E0)[0]

        self.unknown1 = struct.unpack_from("<H", buf, 0x00E4)[0]
        self.unknown2 = struct.unpack_from("<H", buf, 0x00E6)[0]
        self.unknown3 = struct.unpack_from("<H", buf, 0x00E8)[0]

        self.page_count = struct.unpack_from("<H", buf, 0x00EA)[0]

        fmt = "<" + "I" * self.page_count
        self.page_offsets[:] = struct.unpack_from(fmt, buf, 0x00EC)

        for offset in self.page_offsets:
            eop = buf.find("\xF6", offset)
            if eop == -1:
                raise Exception("End of page not found!")
            self.pages.append(Page(buf[offset:eop+1]))

