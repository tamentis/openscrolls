/* 
 * Copyright (c) 2006, Bertrand Janin
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright 
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
 * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, 
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY 
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
 * THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */


#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdint.h>
#include <unistd.h>
#include <strings.h>
#include <SDL.h>
#include "openscroll.h"

/* Apparently the palette's color are on 6 bytes ? */
SDL_Color *
load_palette(char *file)
{
	FILE *fp;
	char *t;
	char *palfile;
	uint16_t i, j;
	SDL_Color *colors = NULL;
	struct stat sb;
	uint32_t size;

	/* Which pal ? (full path or relative to ACD) */
	if (file[0] == '/') {
		int length = strlen(file);
		palfile = malloc(length);
		strlcpy(palfile, file, length+1);
	} else {
		j = strlen(file) + strlen(ACD) + 1;
		palfile = malloc(j);
		snprintf(palfile, j, ACD "%s", file);
	}

	/* Check size */
	stat(palfile, &sb);
	size = sb.st_size;

	/* Load original palette into *t */
	t = malloc(768);
	fp = fopen(palfile, "r");
	if (fp == NULL) {
		printf("Unable to open this palette file (%s).\n", palfile);
		return NULL;
	}

	free(palfile);
	if (size == 768) {
		printf("Loading from a palette file.\n");
		fread(t, 768, 1, fp);
	} else if (size > 768) {
		printf("Loading from an embbed palette file.\n");
		fseek(fp, size-768, SEEK_SET);
		fread(t, 768, 1, fp);
	} else {
		printf("Unable to load selected palette (%s)\n", file);
		fclose(fp);
		return NULL;
	}
	fclose(fp);

	/* Add reserved bytes for BMP */
	colors = malloc(256 * sizeof(SDL_Color));
	for (i=0; i<256; i++) {
		int r=*(t+i*3+0)*4;
		int g=*(t+i*3+1)*4;
		int b=*(t+i*3+2)*4;

		colors[i].r = r;
		colors[i].g = g;
		colors[i].b = b;
	}

	return colors;
}


int
get_header(IMGData *img)
{
	void *header;
	FILE *fp;
	struct stat sb;

	stat(img->fullpath, &sb);
	img->fullsize = sb.st_size;

	/* Read the 12 first bytes */
	header = malloc(12);
	fp = fopen(img->fullpath, "r");
	fread(header, 12, 1, fp);
	fclose(fp);

	img->width = *(uint16_t*)(header+4);
	img->height = *(uint16_t*)(header+6);

	if (img->fullsize == img->width * img->height + 12) {
		printf("This .IMG seems to have a header (%ux%u)\n", img->width, 
				img->height);
		return 1;
	}

	printf("This .IMG has no header, assuming RAW.\n");

	return 0;
}


int
autodetect (IMGData *img)
{
	struct stat sb;

	stat(img->fullpath, &sb);
	img->fullsize = sb.st_size;

	/* Full screen files */
	if (img->fullsize == 64000 || img->fullsize == 64768) {
		printf("File is 64K, assuming fullscreen 320x200.\n");
		img->width = 320;
		img->height = 200;
		if (img->fullsize == 64768) {
			printf("A palette was detected.. trying to load it.\n");
			img->colors = load_palette(img->fullpath);
		}

		return 1;
	}


	/* Weird */
	if (img->fullsize == 68800) {
		printf("Bigger file (320x215?). Need to be fixed.\n");
		img->width = 320;
		img->height = 215;
		return 1;
	}

	/* GRAD0*I0.IMG : Palette ?*/
	if (img->fullsize == 1720) {
		printf("Detected GRAD0*I0.IMG file. Need to be fixed.\n");
		img->width = 10;
		img->height = 172;
		return 1;
	}

	/* ICON00I0.IMG */
	if (img->fullsize == 20480) {
		printf("Icon file detected. (320x64)\n");
		img->width = 320;
		img->height = 64;
		return 1;
	}

	/* ICON00I0.IMG */
	if (img->fullsize == 2916) {
		printf("ITEM01I0.IMG (81x36)\n");
		img->width = 81;
		img->height = 36;
		return 1;
	}

	/* NITE0*I0.IMG */
	if (img->fullsize == 112128) {
		printf("Nite file (876x128). Palette need fix.\n");
		img->width = 876;
		img->height = 128;
		return 1;
	}

	/* This only apply to COMPASS.IMG */
	if (img->fullsize == 4508) {
		printf("COMPASS.IMG detected (322x14).\n");
		img->width = 322;
		img->height = 14;
		return 1;
	}

	return 0;
}

IMGData *
load_img(char *filename)
{
	FILE *fi;
	uint32_t size = 0;
	IMGData *img;

	/* Init the IMGData */
	img = malloc(sizeof(IMGData));
	img->colors = NULL;
	img->data = NULL;
	img->offset = 0;

	/* Get filename from command prompt */
	int fnsize = strlen(ACD) + strlen(filename) + 1;
	img->fullpath = malloc(fnsize);
	snprintf(img->fullpath, fnsize, ACD "%s", filename);

	/* Exists ? Readable ? */
	if (access(img->fullpath, R_OK) == -1) {
		printf("Unable to open Image File '%s'.\n", filename);
		return NULL;
	}

	/* Get size, width and height (detected or guessed) */
	if (get_header(img)) {
		img->offset = 12;
	} else if (!autodetect(img)) {
		printf("Unable to fetch or guess a resolution, giving up.\n");
		return NULL;
	}

	/* Load the default palette if it's still empty */
	if (img->colors == NULL) {
		img->colors = load_palette("PAL.RAW");
	}

	/* Reading data */
	fprintf(stderr, "Opening %s, Fullsize: %d\n", img->fullpath, img->fullsize);
	fi = fopen(img->fullpath, "r");
	img->data = malloc(img->fullsize);
//	while (!feof(fi)) {
		size = fread(img->data, img->fullsize, 1, fi);
//	}
	fprintf(stderr, "Fulldate loaded.\n");
	fclose(fi);

	return img;
}


void
paste_fullscreen(SDL_Surface *screen, IMGData *img)
{
	SDL_Surface *surf;
	SDL_Rect dest;

	surf = SDL_CreateRGBSurfaceFrom(img->data+img->offset, img->width, 
			img->height, 8, img->width, 255, 255, 255, 255);
	SDL_SetPalette(surf, SDL_LOGPAL|SDL_PHYSPAL, img->colors, 0, 256);

	dest.x = 0;
	dest.y = 0;
	dest.w = img->width;
	dest.h = img->height;

	SDL_BlitSurface(surf, NULL, screen, &dest);

	SDL_UpdateRects(screen, 1, &dest);
}

void
wait_for_keymouse()
{
	SDL_Event event;
	while (1) {
		SDL_WaitEvent(&event);
		switch (event.type) {
			case SDL_MOUSEBUTTONDOWN:
			case SDL_KEYDOWN:
				return;
				break;
			case SDL_QUIT:
				exit(0);
		}
	}
}

void
wait_for_button()
{
	SDL_Event event;
	while (1) {
		SDL_WaitEvent(&event);
		switch (event.type) {
			case SDL_MOUSEBUTTONDOWN:
				printf("Mouse button %d pressed at (%d,%d)\n", 
						event.button.button, 
						event.button.x, 
						event.button.y);
				if (event.button.button==1 && 
						event.button.x > 124 && 
						event.button.x < 124+43 && 
						event.button.y > 144 &&
						event.button.y < 144+17) {
					printf("Exiting !\n");
					exit(0);
				}
				if (event.button.button==1 && 
						event.button.x > 70 && 
						event.button.x < 218 && 
						event.button.y > 97 &&
						event.button.y < 116) {
					return;
				}
				break;
			case SDL_QUIT:
				exit(0);
		}
	}
}

