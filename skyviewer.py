#!/usr/bin/python

import sys
import os
import struct

import pygame
from pygame.locals import *


# Main loop default setup
index = 0
see_sun = False


if '-h' in sys.argv or len(sys.argv) != 2:
    print """
     Usage: openscrolls_skyviewer <file>

     Keys:
       PageDown / PageUp    Navigate through the different time periods
       s                    Toggle sun visibility
       q / Escapge          Quit
    """
    exit()


if len(sys.argv) < 2:
    print 'Please specify the file to read.'
    exit()


try:
    fp = open(sys.argv[1], 'rb')
except:
    print 'Unable to open "%s"!' % sys.argv[1]
    exit()


def tuple_to_palette(tup):
    """Convert a tuple into an array of RGB arrays."""
    n = len(tup) / 3
    pal = [ ]
    for i in range(0, n):
        pal.append([ tup[i*3], tup[i*3+1], tup[i*3+2] ])
    return pal


def read_palettes(stream):
    """Take a string and return an array of RGB palettes."""
    palettes = [ ]
    for i in range(0, 32):
        tup = struct.unpack_from('8x768B', stream, 776 * i)
        pal = tuple_to_palette(tup)
        palettes.append(pal)

    return palettes


def keydown(e):
    """Return true if the event 'e' has an interesting value, assigns all
    the keys to their respective functions."""
    global index
    global see_sun

    if e.key == K_ESCAPE or e.key == K_q:
        sys.exit(0)

    elif e.key == K_PAGEDOWN:
        if index < 31:
            index += 1
        return True

    elif e.key == K_PAGEUP:
        if index > 0:
            index -= 1
        return True

    elif e.key == K_s:
        see_sun = not see_sun
        return True
    

def wait_for_key():
    """Will wait for ever until keydown() return True."""
    wait = True
    while wait is True:
        events = pygame.event.get()

        for e in events:
            if e.type == QUIT:
                sys.exit(0)
            elif e.type == KEYDOWN:
                if keydown(e) is True:
                    wait = False
                    break


print 'Loadind data...'


# Read the first 776 * 32 bytes (palettes)
palettes = read_palettes(fp.read(776 * 32))


# Go directly to bitmaps (skipping fadings)
fp.seek(524288, os.SEEK_CUR)


# Preload all the bitmaps
without_sun = [ ]
for i in range(0, 32):
    without_sun.append(fp.read(512 * 220))

with_sun = [ ]
for i in range(0, 32):
    with_sun.append(fp.read(512 * 220))

fp.close()


# PyGame initialization
pygame.init()
window = pygame.display.set_mode((512, 220))
pygame.display.set_caption('OpenScrolls - Sky Viewer')
screen = pygame.display.get_surface()


while True:
    # Choose which array to use, with or without sun
    if see_sun is True:
        pool = with_sun
    else:
        pool = without_sun

    surf = pygame.image.fromstring(pool[index], (512, 220), 'P')
    surf.set_palette(palettes[index])
    screen.blit(surf, (0,0))
    pygame.display.flip()

    wait_for_key()

