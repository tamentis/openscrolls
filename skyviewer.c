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


typedef struct palette_record {
	uint32_t filesize;
	uint16_t f_id;
	uint16_t f_version;
	uint8_t  colors[768];
} prec;


SDL_Color *
get_sdl_palette(uint8_t *c, size_t size)
{
	size_t i;
	SDL_Color *sc;

	sc = malloc(size * sizeof(SDL_Color));

	for (i = 0; i < size; i++) {
		sc[i].r = c[i * 3];
		sc[i].g = c[i * 3 + 1];
		sc[i].b = c[i * 3 + 2];
	}

	return sc;
}


int
main(int ac, char *av[])
{
	SDL_Surface *screen;
	SDL_Surface *s;
	SDL_Color *c;
	unsigned char buf[112640];
	FILE *fp;
	IMGData *img;
	int i;
	prec *palettes;

	if (ac < 2) {
		printf("You need one file as first argument.\n");
		return 1;
	}

	if ( SDL_Init(SDL_INIT_AUDIO|SDL_INIT_VIDEO) < 0 ) {
		fprintf(stderr, "Unable to init SDL: %s\n", SDL_GetError());
		exit(1);
	}
	atexit(SDL_Quit);

	screen = SDL_SetVideoMode(512, 220, 16, SDL_SWSURFACE);
	if ( screen == NULL ) {
		fprintf(stderr, "Unable to set 320x200x16bit video: %s\n", SDL_GetError());
		exit(1);
	}

	SDL_WM_SetCaption("OpenScrolls v" OSCROLLVER " - ImgViewer", NULL);

	palettes = malloc(32 * sizeof(prec));

	fp = fopen(ACD "SKY00.DAT", "rb");
	fread(palettes, 776, 32, fp);

	fprintf(stderr, " X 2 size: %d\n", palettes[2].filesize);

	/* Skip the fade tables. */
	fseek(fp, 524288, SEEK_CUR);

	for (i = 0; i < 32; i++) {
		fread(buf, 512, 220, fp);

		s = SDL_CreateRGBSurfaceFrom(buf, 512, 220, 8, 512, 255, 255, 255, 255);
		c = get_sdl_palette(palettes[i].colors, 256);
		SDL_SetPalette(s, SDL_LOGPAL|SDL_PHYSPAL, c, 0, 256);

		SDL_BlitSurface(s, NULL, screen, NULL);
		SDL_Flip(screen);
		wait_for_keymouse();
	}

	for (i = 0; i < 32; i++) {
		fread(buf, 512, 220, fp);

		s = SDL_CreateRGBSurfaceFrom(buf, 512, 220, 8, 512, 255, 255, 255, 255);
		c = get_sdl_palette(palettes[i].colors, 256);
		SDL_SetPalette(s, SDL_LOGPAL|SDL_PHYSPAL, c, 0, 256);

		SDL_BlitSurface(s, NULL, screen, NULL);
		SDL_Flip(screen);
		wait_for_keymouse();
	}

//	img = load_img(av[1]);

//	paste_fullscreen(screen, img);
	fclose(fp);


	return 0;
}

