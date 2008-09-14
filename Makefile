## Makefile for OpenScrolls
## 

VERSION=0.2.0

CFLAGS=`sdl-config --cflags`
LIBFLAGS=`sdl-config --libs`
OPTIONS=-g -O2 -Wall -DOSCROLLVER=\"$(VERSION)\" 
DEST=/usr/local/bin

VIEWER=openscrolls_imgviewer
MENU=openscrolls_menu

all: $(VIEWER) $(MENU) $(SKYVIEW)

IMGVIEWER_OBJECTS=imgviewer.o openscroll.o strlcpy.o
$(VIEWER): $(IMGVIEWER_OBJECTS)
	$(CC) $(OPTIONS) $(IMGVIEWER_OBJECTS) $(LIBFLAGS) -o $(VIEWER)

MENU_OBJECTS=menu.o openscroll.o strlcpy.o
$(MENU): $(MENU_OBJECTS)
	$(CC) $(OPTIONS) $(MENU_OBJECTS) $(LIBFLAGS) -o $(MENU)

.c.o: openscroll.h
	$(CC) $(OPTIONS) $(CFLAGS) -c $<

clean:
	rm -f $(VIEWER) $(MENU) $(SKYVIEW) *.o *.pyc

install:
	install -m 755 $(VIEWER) $(DEST)
