#!/usr/bin/python

import Tkinter 
import ImageTk
import sys
from daggerfall.fonts import Font

if len(sys.argv) < 2:
    print("usage: %s filename" % sys.argv[0])
    sys.exit(-1)

font = Font(sys.argv[1])

print("Font loaded: %s (%dx%d) with %d glyphs" % (font.filename, font.max_width,
                                                  font.max_height, len(font.glyphs)))

root = Tkinter.Tk()
im = font.get_map("This is a brilliant font reader.")
tkimage = ImageTk.PhotoImage(im)
tklabel = Tkinter.Label(root, image=tkimage)
tklabel.pack() # Put it in the display window

def goodbye(event):
    root.destroy()

root.bind("<Escape>", goodbye)
    
root.mainloop() # Start the GUI
