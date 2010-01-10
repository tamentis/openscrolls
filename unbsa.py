#!/usr/bin/python

import os
import sys
import struct

import bsa


if '-h' in sys.argv or len(sys.argv) != 2:
    print """
     Usage: openscrolls_unbsa <file>

     Extracts all the records within a BSA file.
    """
    exit()


file = bsa.BSAFile(sys.argv[1])


print 'This BSA file holds %d records of type %x (%s).' % ( file.count, file.type,
        bsa.TypeDescription[file.type]['Text'])

file.extract()


