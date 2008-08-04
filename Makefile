## Makefile for OpenScrolls
## 

VERSION=0.0.1

CFLAGS=`sdl-config --cflags`
LIBFLAGS=`sdl-config --libs`
OPTIONS=-g -O2 -Wall -DOSCROLLVER=\"$(VERSION)\" 
DEST=/usr/local/bin

VIEWER=openscrolls_imgviewer
MENU=openscrolls_menu
SKYVIEW=skyview

all: $(VIEWER) $(MENU) $(SKYVIEW)

SKYVIEW_OBJECTS=skyviewer.o openscroll.o strlcpy.o
$(SKYVIEW): $(SKYVIEW_OBJECTS)
	$(CC) $(OPTIONS) $(SKYVIEW_OBJECTS) $(LIBFLAGS) -o $(SKYVIEW)

IMGVIEWER_OBJECTS=imgviewer.o openscroll.o strlcpy.o
$(VIEWER): $(IMGVIEWER_OBJECTS)
	$(CC) $(OPTIONS) $(IMGVIEWER_OBJECTS) $(LIBFLAGS) -o $(VIEWER)

MENU_OBJECTS=menu.o openscroll.o strlcpy.o
$(MENU): $(MENU_OBJECTS)
	$(CC) $(OPTIONS) $(MENU_OBJECTS) $(LIBFLAGS) -o $(MENU)

.c.o: openscroll.h
	$(CC) $(OPTIONS) $(CFLAGS) -c $<

clean:
	rm -f $(VIEWER) $(MENU) $(SKYVIEW) *.o

install:
	install -m 755 $(VIEWER) $(DEST)
