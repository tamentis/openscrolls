#!/usr/bin/env python

from distutils.core import setup
import py2exe

setup(windows=[{
  "script": "book_reader.py",
  "icon_resources": [(1, "openscrolls.ico")]
}])
