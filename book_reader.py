#!/usr/bin/env python

import sys
import os.path
import daggerfall
from daggerfall.books import Book, Page, Line
from daggerfall.fonts import Font
from Tkinter import *
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import ImageTk
import Image

class BookRenderer:
    appname = "OpenScrolls - Daggerfall Book Reader"
    bg_filename = "BOOK00I0.IMG"
    palette_filename = "PAL.RAW"
    width = 320
    height = 200

    def __init__(self):
        self.root = None
        self.book = None
        self.fonts = { }
        self.tklabel = None
        self.current_page = 0
        self.top_margin = 20
        self.left_margin = 10
        self.background = None

    def get_intro(self):
        """Return a 'Book' for the intro page."""

        book = Book()
        book.title = "Welcome!"

        page = Page()
        book.pages.append(page)
        page.add_line("")
        page.add_line("")
        page.add_line("")
        page.add_header("Welcome to the Daggerfall")
        page.add_line("")
        page.add_header("Book Reader!")
        page.add_lines("""\n\n
Right-Click anywhere on the screen to get to the main menu. We
defined a lot of shortcuts to switch between pages, you can
also use the buttons at the bottom of the window.""")

        page = Page()
        book.pages.append(page)
        page.add_lines("\n\nYup, that's page two =)\n\nHit Page Up to go back.")

        return book

    def get_background(self):
        if self.background is not None:
            return self.background.copy()

        fp = open(self.get_abspath(self.bg_filename), "rb")
        bgdata = fp.read()
        fp.close()

        fp = open(self.get_abspath(self.palette_filename), "rb")
        paldata = [ord(x) * 4 for x in fp.read()]
        fp.close()

        im = Image.fromstring("P", (self.width, self.height), bgdata)
        im.putpalette(paldata)

        self.background = im

        return im.copy()

    def set_title(self):
        self.root.title("%s - \"%s\"" % (self.appname, self.book.title))

    def set_book(self, filename):
        self.book = Book(filename)
        self.current_page = 0
        if self.root is not None:
            self.set_title()
            self.draw_page()

    def draw_page(self):
        im = self.get_background()

        page = self.book.pages[self.current_page]

        for line in page.lines:
            line_image = line.get_image(color=0x91)
            line_image_shadow = line.get_image(color=0x9C)
            if line_image is None:
                continue
            x, y = line.get_pos()
            x += self.left_margin
            y += self.top_margin
            mask = line_image.copy()
            mask = Image.eval(mask, lambda a: 255 if a != 0 else 0)
            im.paste(line_image_shadow, (x+1, y+1), mask=mask)
            im.paste(line_image, (x, y), mask=mask)

        im = im.resize((640, 400), Image.NEAREST)

        # Keep the old label and destroy it after to reduce flickering
        oldlabel = self.tklabel

        self.tkimage = ImageTk.PhotoImage(im)
        self.tklabel = Label(self.root, image=self.tkimage)

        self.tklabel.pack()
        if oldlabel is not None:
            oldlabel.destroy()

    def exit(self=None, event=None):
        self.root.destroy()

    def next_page(self=None, event=None):
        if self.current_page < len(self.book.pages) - 1:
            self.current_page += 1
            self.draw_page()

    def previous_page(self=None, event=None):
        if self.current_page > 0:
            self.current_page -= 1
            self.draw_page()

    def page_prompt(self=None, event=None):
        newpage = tkSimpleDialog.askinteger("Select page", "Enter new page:",
                        initialvalue=(self.current_page + 1),
                        minvalue=1,
                        maxvalue=len(self.book.pages))
        if newpage:
            self.current_page = newpage - 1
            self.draw_page()

    def onclick(self=None, event=None):
        self.menu.unpost()

        # all buttons are below this line
        if event.y < 365:
            return

        if event.x > 362 and event.x < 391:
            self.previous_page()
        elif event.x > 416 and event.x < 447:
            self.next_page()
        elif event.x > 483 and event.x < 532:
            self.page_prompt()
        elif event.x > 557 and event.x < 617:
            self.exit()
        #else:
        #    print(event.x, event.y)

    def wheel(self=None, event=None):
        if event.num == 5 or event.delta == -120:
            self.next_page()
        if event.num == 4 or event.delta == 120:
            self.previous_page(event)

    def get_abspath(self, filename, cdpath=None):
        return daggerfall.get_abspath(filename, cdpath)

    def open_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def valid_cdpath(self, cdpath):
        bg_fullpath = self.get_abspath(self.bg_filename, cdpath=cdpath)
        return (bg_fullpath is None)

    def choose_cdpath(self):
        dirname = tkFileDialog.askdirectory(parent=self.root,
                        initialdir="/", 
                        title="Where is your Daggerfall CD?")

        # Cancel
        if dirname == () or dirname == "":
            return

        # Invalid path all together
        if not os.path.exists(dirname) or not os.path.isdir(dirname):
            again = tkMessageBox.askretrycancel(title="Invalid",
                           message="The path you selected is invalid!")
            if again:
                return self.choose_cdpath()
            else:
                sys.exit(-1)

        # Not a Daggerfall CD/Install
        if self.valid_cdpath(dirname):
            again = tkMessageBox.askretrycancel(title="Data not found",
                           message="The path entered does not seem to contain "+
                                   "the proper Data, do you want to retry and "+
                                   "select a different path?")
            if again:
                return self.choose_cdpath()
            else:
                sys.exit(-1)

        daggerfall.set_cdpath(dirname)

    def choose_book(self):
        start = daggerfall.cdpath or "."
        filename = tkFileDialog.askopenfilename(parent=self.root,
                        initialdir=start, 
                        filetypes=[ ("Daggerfall Book", "*.TXT") ],
                        title="Select a book file (.TXT)")
        if filename == "":
            return
        try:
            self.set_book(filename)
        except:
            again = tkMessageBox.askretrycancel(title="Invalid",
                           message="This doesn't seem to be a valid book.")
            if again:
                return self.choose_book()

    def run(self):
        cdpath = daggerfall.get_cdpath()
        if cdpath is None and self.valid_cdpath(cdpath):
            tmproot = Tk()
            tmproot.withdraw()

            tkMessageBox.showinfo(title="Daggerfall CD",
                message="Welcome to the Daggerfall Book Reader!\n\n" +
                    "Since we couldn't detect your Daggerfall CD, you will " +
                    "be prompted to choose its location manually.\n\n" +
                    "You can also choose your installation path if the game " +
                    "was installed using the \"Full\" installation.")
            self.choose_cdpath()
            tmproot.destroy()

        self.root = Tk()
        self.root.resizable(0, 0)
        self.root.title(self.appname)

        if self.book is None:
            self.book = self.get_intro()

        self.set_title()
        self.draw_page()

        # Exit shortcuts
        self.root.bind("<Escape>", self.exit)
        self.root.bind("q", self.exit)

        # Next and previous for everyone
        self.root.bind("l", self.next_page)
        self.root.bind("j", self.next_page)
        self.root.bind("<Up>", self.next_page)
        self.root.bind("<Left>", self.next_page)
        self.root.bind("<Next>", self.next_page)
        self.root.bind("<space>", self.next_page)
        self.root.bind("h", self.previous_page)
        self.root.bind("k", self.previous_page)
        self.root.bind("<Prior>", self.previous_page)
        self.root.bind("<Down>", self.previous_page)
        self.root.bind("<Right>", self.previous_page)
        self.root.bind("<BackSpace>", self.previous_page)

        # Mousewheel for win and nix
        self.root.bind("<MouseWheel>", self.wheel)
        self.root.bind("<Button-4>", self.wheel)
        self.root.bind("<Button-5>", self.wheel)

        # Clicking on stuff
        self.root.bind("<Button-1>", self.onclick)

        # Right click menu
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="Open Book", command=self.choose_book)
        self.menu.add_command(label="Set Daggerfall CD Path", command=self.choose_cdpath)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.exit)
        self.root.bind("<Button-3>", self.open_menu)

        self.root.mainloop() # Start the GUI


renderer = BookRenderer()
if len(sys.argv) > 1:
    renderer.set_book(sys.argv[1])
renderer.run()

"""
print("Title:     {0}".format(book.title))
print("Author:    {0}".format(book.author))
print("Topics:")
for topic in book.topics:
    print(" - {0}".format(topic))
print("Naughty:   {0}".format(book.is_naughty))
print("Price:     {0}".format(book.price))
print("Unknown1:  {0}".format(book.unknown1))
print("Unknown2:  {0}".format(book.unknown2))
print("Unknown3:  {0}".format(book.unknown3))
print("PageCount: {0}".format(book.page_count))
print("PageOffsets:")
for offset in book.page_offsets:
    print(" - 0x%04X" % offset)
print("Pages:")
for page in book.pages:
    print(" - {0}".format(page.markup))
"""

