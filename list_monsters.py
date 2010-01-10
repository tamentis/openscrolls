#!/usr/bin/python

import os
import sys
import struct

import bsa
import daggerfall.casttypes as casttypes


class Tolerance():
    def __init__(self, byte):

        self.toParalysis = bool(byte & casttypes.PARALYSIS)
        self.toMagic = bool(byte & casttypes.MAGIC)
        self.toPoison = bool(byte & casttypes.POISON)
        self.toFire = bool(byte & casttypes.POISON)
        self.toFrost = bool(byte & casttypes.FROST)
        self.toShock = bool(byte & casttypes.SHOCK)
        self.toDisease = bool(byte & casttypes.SHOCK)

    def toString(self):
        a = [ ]
        if self.toParalysis is True:
            a.append('to Paralysis')
        if self.toMagic is True:
            a.append('to Magic')
        if self.toPoison is True:
            a.append('to Poison')
        if self.toFire is True:
            a.append('to Fire')
        if self.toFrost is True:
            a.append('to Frost')
        if self.toShock is True:
            a.append('to Shock')
        if self.toDisease is True:
            a.append('to Disease')

        return ', '.join(a)


class Monster():
    def __init__(self, string):
        tup = struct.unpack('BBBBHBBBBBHBHBBBBBBBBBB16s30x', string)

        self.name = tup[23].partition('\0')[0]

        self.resistance = Tolerance(tup[0])
        self.immunity = Tolerance(tup[1])
        self.low_tolerance = Tolerance(tup[2])
        self.critical_weakness = Tolerance(tup[3])

        self.acute_hearing = bool(tup[4] & 1)
        self.athleticism = bool(tup[4] & 2)
        self.adrenaline_rush = bool(tup[4] & 4)
        self.no_regen_sp = bool(tup[4] & 8)
        self.sun_damage = bool(tup[4] & 16)
        self.holy_damage = bool(tup[4] & 32)

        sp_mult = {
            0: 3.0,
            1: 2.0,
            2: 1.75,
            3: 1.5,
            4: 1.0
        }

        print 'tup4 %016x' % tup[4]

        self.sp_in_dark = (tup[4] & 0x00C0) >> 8
        self.sp_in_light = (tup[4] & 0x0300) >> 10
        self.total_sp = sp_mult[(tup[4] & 0x1C00) >> 12]
        



if '-h' in sys.argv or len(sys.argv) != 2:
    print """
     Usage: openscrolls_monster <MONSTER.BSA>

     Display all the information stored in MONSTER.BSA.
    """
    exit()


file = bsa.BSAFile(sys.argv[1])


for i in range(0, 43):
    data = file.get_record('ENEMY0%02d.CFG' % i)

    monster = Monster(data)

    print """
Name:               %s
Resistances:        %s
Immunities:         %s
Low Tolerance:      %s
Critical Weakness:  %s

Acute Hearing:      %r
Athleticism:        %r
Adrenaline Rush:    %r
No Regen SP:        %r
Sun Damage:         %r
Holy Damage:        %r

SP in dark:         %d
SP in light:        %d
Total SP:           %f

""" % (monster.name, monster.resistance.toString(), monster.immunity.toString(),
       monster.low_tolerance.toString(), monster.critical_weakness.toString(),
       monster.acute_hearing, monster.athleticism, monster.adrenaline_rush,
       monster.no_regen_sp, monster.sun_damage, monster.holy_damage,
       monster.sp_in_dark, monster.sp_in_light, monster.total_sp)


#print data

