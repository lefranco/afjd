#include <math.h>

#include "../solveur/define.h"
#include "define2.h"
#include "../solveur/struct.h"
#include "struct2.h"
#include "../solveur/includes.h"
#include "../solveur/protos.h"
#include "protos2.h"
#include "../solveur/datas.h"
#include "datas2.h"

#define NPAYS 7
#define TLEGENDE 100
#define TJOUEUR 100
#define TORDRE 100
#define TVOPA 14

/* Pour le texte */
#define ratiox 7  /* Largeur en pixel d'un caractere */
#define ratioy 13 /* Hauteur en pixel d'un caractere */
#define mx  7       /* Marge pour eviter le bord */
#define my  7       /* Marge pour eviter le bord */

#include <gd.h>
#include <gdfontt.h>
#include <gdfonts.h>
#include <gdfontmb.h>
#include <gdfontl.h>
#include <gdfontg.h>

gdFontPtr gdFontGetTiny(void);
gdFontPtr gdFontGetSmall(void);
gdFontPtr gdFontGetMediumBold(void);
gdFontPtr gdFontGetLarge(void);
gdFontPtr gdFontGetGiant(void);

char fontevariable[] = "systeme/fonts/timesbd.ttf";
char fontefixe[] = "systeme/fonts/courbd.ttf";

int brect[8];

static void metcroix(gdImagePtr, int, int, int);
static void metdrapeau(gdImagePtr, int, int, int, int);
static int cherchepaysvopa(int);
static void localisecentre(_CENTRE *, int *, int *);
static void metcentre(gdImagePtr, int, int, int, int, int, char *, BOOL);
static void metmarqueflottevopa(gdImagePtr, int, int, int, int);
static void metunitevopa(gdImagePtr, int, int, int, int, int);
static void metarmeevopa(gdImagePtr, int, int, int, int, int);
static void metflottevopa(gdImagePtr, int, int, int, int, int);
static void metarmee(gdImagePtr, int, int, int, int, int, char *, BOOL);
static void metflotte(gdImagePtr, int, int, int, int, int, char *, BOOL);
static void metunitedelogee(gdImagePtr, int, int, int, int, char *);
static void metzoneinterdite(gdImagePtr, int, int, int, int);
static void partie(gdImagePtr, char *, int);
static void saison(gdImagePtr, char *, int, int);
static void datelimite(gdImagePtr, char *, int, int);
static void titre1(gdImagePtr, char *, int);
static void titre2(gdImagePtr, char *, int);
static void gdate(gdImagePtr, int);
static void cr(gdImagePtr, char *, int);
static void legende(gdImagePtr, int col1[], int col2[], char *, int, int);
static void localisecentre(_CENTRE *zone, int *x, int *y);
static void localisezone(_ZONE *, int *, int *);
static void localiseregion(_REGION *, int *, int *);
static _COULEUR *cherchecouleur(_PAYS *);
static void allouecouleur(gdImagePtr, int *, int *, int, int, int,
		const char *, const char *);
static void infospreajustements(gdImagePtr, int col1[], int col2[], int);
static int calculehauteurtexte(gdImagePtr, int *, int *, int *);
static void remplittexte(gdImagePtr, int, int, int, int);
static void inseretag(gdImagePtr, char *, int);
static BOOL partiegagnee(void);

static int colvopa[NPAYS];
static int blancvopa, noirvopa;

#ifndef __CYGWIN__
#define gdFontGetTiny() gdFontTiny
#define gdFontGetSmall() gdFontSmall
#define gdFontGetMediumBold() gdFontMediumBold
#define gdFontGetLarge() gdFontLarge
#define gdFontGetGiant() gdFontGiant
#endif

static void metcroix(gdImagePtr im, int x, int y, int couleur) {

	gdImageSetPixel(im, x + 1, y, couleur);
	gdImageSetPixel(im, x - 1, y, couleur);
	gdImageSetPixel(im, x, y + 1, couleur);
	gdImageSetPixel(im, x, y - 1, couleur);
	gdImageSetPixel(im, x, y, couleur);

}

static void metdrapeauhasbro(gdImagePtr im, int x, int y, int couleur1,
		int couleur2) {

	gdPoint p[4];

	p[0].x = x - 5;
	p[0].y = y - 5;

	p[1].x = x + 5;
	p[1].y = y - 5;

	p[2].x = x + 5;
	p[2].y = y + 5;

	p[3].x = x - 5;
	p[3].y = y + 5;

	gdImageSetThickness(im, 1);
	gdImageSetAntiAliased(im, couleur2);

	gdImageFilledPolygon(im, p, 4, couleur1);
	gdImagePolygon(im, p, 4, gdAntiAliased);

}

static void metdrapeau(gdImagePtr im, int x, int y, int couleur1, int couleur2) {
	if (OPTIONV)
		metarmeevopa(im, x, y, couleur1, TVOPA / 2, 1);
	else
		metdrapeauhasbro(im, x, y, couleur1, couleur2);
}

static void metcentrevopa(gdImagePtr im, int x, int y, int couleur1,
		int couleur2) {
	couleur2 = couleur2; /* evite un avertissement du compilateur */
	metarmeevopa(im, x, y, couleur1, (TVOPA * 2) / 3, 1);
}

/*
 static void metcentre18centres(gdImagePtr im, int x, int y, int couleur1, int couleur2)
 {

 gdImageSetThickness(im,1);
 gdImageSetAntiAliased(im,couleur2);

 gdImageFilledArc(im, x,y,9,9,0,360, couleur1,gdArc);
 gdImageArc(im, x,y,9,9,0,360, couleur2);
 }
 */

/*
 static void metcentreonline(gdImagePtr im, int x, int y, int couleur1, int couleur2)
 {
 gdImageSetThickness(im,1);
 gdImageSetAntiAliased(im,couleur2);

 gdImageFilledRectangle(im, x-5,y-5,x+5,y+5, couleur1);
 gdImageRectangle(im, x-5,y-5,x+5,y+5, couleur2);
 }
 */

static void metcentrehasbro(gdImagePtr im, int x, int y, int couleur1,
		int couleur2) {
	gdImageSetThickness(im, 1);
	gdImageSetAntiAliased(im, couleur2);

	gdImageFilledRectangle(im, x - 4, y - 4, x + 4, y + 4, couleur1);
	gdImageRectangle(im, x - 4, y - 4, x + 4, y + 4, couleur2);
}

static void metcentredescartes(gdImagePtr im, int x, int y, int couleur1,
		int couleur2) {
	int w, h, ec;

	w = 11;
	h = 5;
	ec = 2;

	gdImageSetThickness(im, 1);
	gdImageSetAntiAliased(im, couleur2);

	gdImageFilledRectangle(im, x - w / 2, y - ec, x + w / 2, y + ec, couleur1);

	gdImageFilledArc(im, x, y + ec, w, h, 360, 180, couleur1, gdArc);
	gdImageArc(im, x, y + ec, w, h, 360, 180, couleur2);

	gdImageFilledArc(im, x, y - ec, w, h, 0, 360, couleur1, gdArc);
	gdImageArc(im, x, y - ec, w, h, 0, 360, couleur2);

	gdImageLine(im, x - w / 2, y - ec, x - w / 2, y + ec, gdAntiAliased);
	gdImageLine(im, x + w / 2, y - ec, x + w / 2, y + ec, gdAntiAliased);

}

static void metcentre(gdImagePtr im, int x, int y, int couleur1, int couleur2,
		int coultag, char *nom, BOOL croix) {
	if (OPTIOND)
		metcentredescartes(im, x, y, couleur1, couleur2);
	else if (OPTIONV)
		metcentrevopa(im, x, y, couleur1, couleur2);
	else
		metcentrehasbro(im, x, y, couleur1, couleur2);

	if (croix)
		metcroix(im, x, y, couleur2);

	if (nom) {
		if (OPTIONC)
			gdImageString(im, gdFontGetTiny(), x + 6, y + 1,
					(unsigned char *) nom, coultag);
		else
			gdImageString(im, gdFontGetMediumBold(), x + 6, y + 1,
					(unsigned char *) nom, coultag);
	}

}

static int cherchepaysvopa(int coul) {
	int i;

	for (i = 0; i < NPAYS; i++)
		if (colvopa[i] == coul)
			return i;

	assert(FALSE);
	return -1; /* evite un avertissement */
}

static void metunitevopa(gdImagePtr im, int x, int y, int pays, int taille,
		int epaisseur) {
	gdPoint p[3];

	gdImageSetThickness(im, epaisseur);
	gdImageSetAntiAliased(im, noirvopa);

	switch (pays) {
	case 0: /* ALLEMAGNE */
		taille -= 2;
		gdImageFilledRectangle(im, x - taille / 2, y - taille / 2, x + taille
				/ 2, y + taille / 2, noirvopa);
		break;
	case 1: /* ANGLETERRE */
		gdImageFilledArc(im, x, y, taille, taille, 0, 360, noirvopa, gdArc);
		break;
	case 2: /* AUTRICHE */
		gdImageFilledArc(im, x, y, taille, taille, 0, 360, blancvopa, gdArc);
		gdImageArc(im, x, y, taille, taille, 0, 360, noirvopa);
		break;
	case 3: /* FRANCE */
		taille -= 2;
		gdImageFilledRectangle(im, x - taille / 2, y - taille / 2, x + taille
				/ 2, y + taille / 2, blancvopa);
		gdImageRectangle(im, x - taille / 2, y - taille / 2, x + taille / 2, y
				+ taille / 2, noirvopa);
		break;
	case 4: /* ITALIE */
		p[0].x = x - taille / 2;
		p[0].y = y - taille / 2;
		p[1].x = x + taille / 2;
		p[1].y = y - taille / 2;
		p[2].x = x;
		p[2].y = y + taille / 2;
		gdImageFilledPolygon(im, p, 3, noirvopa);
		break;
	case 5: /* RUSSIE */
		p[0].x = x + taille / 2;
		p[0].y = y + taille / 2;
		p[1].x = x - taille / 2;
		p[1].y = y + taille / 2;
		p[2].x = x;
		p[2].y = y - taille / 2;
		gdImageFilledPolygon(im, p, 3, blancvopa);
		gdImagePolygon(im, p, 3, noirvopa);
		break;
	case 6: /* TURQUIE */
		/* remplissage */
		gdImageFilledArc(im, x + taille / 4, y, taille, taille, 90, 270,
				blancvopa, gdArc);
		/* exterieur */
		gdImageArc(im, x + taille / 4, y, taille, taille, 90, 270, noirvopa);
		/* interieur */
		gdImageArc(im, x + (taille * 7) / 8, y, (taille * 3) / 2, (taille * 3)
				/ 2, 132, 228, noirvopa);
		break;
	default:
		assert(FALSE);
	}

}

static void metmarqueflottevopa(gdImagePtr im, int x, int y, int taille,
		int epaisseur) {
	gdImageSetThickness(im, epaisseur);
	gdImageLine(im, x - (taille * 4) / 5, y, x + (taille * 4) / 5, y, noirvopa);
}

static void metarmeevopa(gdImagePtr im, int x, int y, int couleur1, int taille,
		int epaisseur) {
	int pays;

	pays = cherchepaysvopa(couleur1);
	metunitevopa(im, x, y, pays, taille, epaisseur);
}

static void metflottevopa(gdImagePtr im, int x, int y, int couleur1,
		int taille, int epaisseur) {
	int pays;

	pays = cherchepaysvopa(couleur1);
	metunitevopa(im, x, y, pays, taille, epaisseur);
	metmarqueflottevopa(im, x, y, taille, epaisseur);

}

/*
 static void metarmee18centres(gdImagePtr im, int x, int y, int couleur1, int couleur2)
 {
 gdPoint p1[4], p2[4], p3[4];

 gdImageSetThickness(im,1);
 gdImageSetAntiAliased(im,couleur2);

 p1[0].x = p2[0].x = p3[0].x = x + 1;
 p1[0].y = p2[0].y = p3[0].y = y - 4;

 p1[1].x = p3[1].x = x - 6;
 p1[1].y = p3[1].y = y - 4;

 p1[2].x = x - 6;
 p1[2].y = y + 7;

 p1[3].x = p2[3].x = x + 1;
 p1[3].y = p2[3].y = y + 7;

 p2[1].x = p3[3].x = x + 4;
 p2[1].y = p3[3].y = y - 8;

 p2[2].x = x + 4;
 p2[2].y = y + 3;

 p3[2].x = x - 2;
 p3[2].y = y - 8;

 gdImageFilledPolygon(im,p1,4, couleur1);
 gdImagePolygon(im,p1,4, gdAntiAliased);

 gdImageFilledPolygon(im,p2,4, couleur1);
 gdImagePolygon(im,p2,4, gdAntiAliased);

 gdImageFilledPolygon(im,p3,4, couleur1);
 gdImagePolygon(im,p3,4, gdAntiAliased);

 }
 */

/*
 static void metarmeeonline(gdImagePtr im, int x, int y, int couleur1, int couleur2)
 {
 gdImageSetThickness(im,1);
 gdImageSetAntiAliased(im,couleur2);

 *//* gros  ovale *//*
 gdImageFilledArc(im, x,y+4,30,13,0,360, couleur1,gdArc);
 gdImageArc(im, x,y+4,30,13,0,360, couleur2);
 *//* petit  ovale *//*
 gdImageFilledArc(im, x,y-6,20,10,0,360, couleur1,gdArc);
 gdImageArc(im, x,y-6,20,10,0,360, couleur2);
 *//* chenilles *//*
 gdImageArc(im, x,y+7,26,5,0,360, couleur2);
 *//* canon *//*
 gdImageSetThickness(im,3);
 gdImageLine(im,x-10,y-6,x-15,y-6,couleur2);

 }
 */

static void metarmeehasbro(gdImagePtr im, int x, int y, int couleur1,
		int couleur2) {
	gdPoint p1[4], p2[3], p3[4];
	int i;

	/* socle */
	p1[0].x = x - 15;
	p1[0].y = y + 6;
	p1[1].x = x - 15;
	p1[1].y = y + 9;
	p1[2].x = x + 6;
	p1[2].y = y + 9;
	p1[3].x = x + 6;
	p1[3].y = y + 6;

	gdImageSetThickness(im, 1);
	gdImageSetAntiAliased(im, couleur2);

	gdImageFilledPolygon(im, p1, 4, couleur1);
	gdImagePolygon(im, p1, 4, gdAntiAliased);

	/* coin */
	p2[0].x = x - 9;
	p2[0].y = y + 6;
	p2[1].x = x - 4;
	p2[1].y = y + 6;
	p2[2].x = x - 7;
	p2[2].y = y + 3;
	gdImageFilledPolygon(im, p2, 3, couleur1);

	/* roue extérieure remplissage */
	for (i = 10; i <= 15; i++)
		gdImageArc(im, x, y, i, i, 0, 360, couleur1);

	/* rayons part camembert */
	gdImageFilledArc(im, x, y, 10, 10, 135, 270, couleur1, gdArc);

	/* roue intérieure */
	gdImageFilledArc(im, x, y, 4, 4, 0, 360, couleur1, gdArc);

	/* canon */
	p3[0].x = x - 2;
	p3[0].y = y - 7;
	p3[1].x = x + 4;
	p3[1].y = y - 15;
	p3[2].x = x + 5;
	p3[2].y = y - 13;
	p3[3].x = x;
	p3[3].y = y - 7;

	gdImageFilledPolygon(im, p3, 4, couleur1);
	gdImagePolygon(im, p3, 4, gdAntiAliased);

	/* rayons de la roue */
	gdImageSetThickness(im, 1);
	gdImageLine(im, x + 2, y, x + 5, y, couleur2); /* a */
	gdImageLine(im, x + 2, y + 2, x + 4, y + 4, couleur2); /* b */
	gdImageLine(im, x, y + 2, x, y + 5, couleur2); /* c */
	gdImageLine(im, x - 2, y + 2, x - 4, y + 4, couleur2); /*  d */
	gdImageLine(im, x - 2, y, x - 4, y, couleur2); /* e */
	gdImageLine(im, x - 2, y - 2, x - 4, y - 4, couleur2); /*  f */
	gdImageLine(im, x, y - 2, x, y - 5, couleur2); /*  g */
	gdImageLine(im, x + 2, y - 2, x + 4, y - 4, couleur2); /* h */

	/* cercle autour roue extérieure */
	gdImageSetThickness(im, 1);
	gdImageArc(im, x, y, 15, 15, 120, 300, couleur2);
	gdImageArc(im, x, y, 15, 15, 270, 55, couleur2);

	/* cercle autour roue intérieur */
	gdImageArc(im, x, y, 10, 10, 0, 360, couleur2);

	/* cercle autour essieu */
	gdImageArc(im, x, y, 4, 4, 0, 360, couleur2);

	/* extérieur coin */
	gdImageLine(im, x - 7, y + 3, x - 9, y + 6, couleur2);
}

static void metarmeedescartes(gdImagePtr im, int x, int y, int couleur1,
		int couleur2) {
	gdPoint p1[4], p2[3];

	p1[0].x = p2[0].x = x + 2;
	p1[0].y = p2[0].y = y + 6;

	p1[1].x = p2[1].x = x + 8;
	p1[1].y = p2[1].y = y - 2;

	p1[2].x = x - 2;
	p1[2].y = y - 9;

	p1[3].x = x - 9;
	p1[3].y = y - 2;

	p2[2].x = x + 14;
	p2[2].y = y + 5;

	gdImageSetThickness(im, 1);
	gdImageSetAntiAliased(im, couleur2);

	gdImageFilledPolygon(im, p1, 4, couleur1);
	gdImagePolygon(im, p1, 4, gdAntiAliased);

	gdImageFilledPolygon(im, p2, 3, couleur1);
	gdImagePolygon(im, p2, 3, gdAntiAliased);

	gdImageFilledPolygon(im, p2, 3, couleur1);
	gdImagePolygon(im, p2, 3, gdAntiAliased);

}

/*
 static void metflotte18centres(gdImagePtr im, int x, int y, int couleur1, int couleur2)
 {

 gdPoint p1[4], p2[4], p3[4];

 p1[0].x = p2[0].x = p3[0].x = x;
 p1[0].y = p2[0].y = p3[0].y = y;

 p1[1].x = p3[1].x = x - 8;
 p1[1].y = p3[1].y = y;

 p1[2].x = x - 12;
 p1[2].y = y + 5;

 p1[3].x = p2[1].x = x + 4;
 p1[3].y = p2[1].y = y + 5;

 p2[2].x = x + 7;
 p2[2].y = y;

 p2[3].x = p3[3].x = x + 2;
 p2[3].y = p3[3].y = y - 4;

 p3[2].x = x - 4;
 p3[2].y = y - 4;

 gdImageSetThickness(im,1);
 gdImageSetAntiAliased(im,couleur2);

 gdImageFilledPolygon(im,p1,4, couleur1);
 gdImagePolygon(im,p1,4, gdAntiAliased);

 gdImageFilledPolygon(im,p2,4, couleur1);
 gdImagePolygon(im,p2,4, gdAntiAliased);

 gdImageFilledPolygon(im,p3,4, couleur1);
 gdImagePolygon(im,p3,4, gdAntiAliased);

 }
 */

/*
 static void metflotteonline(gdImagePtr im, int x, int y, int couleur1, int couleur2)
 {
 gdPoint p1[9];

 p1[0].x = x - 4;
 p1[0].y = y;
 p1[1].x = x - 16;
 p1[1].y = y;
 p1[2].x = x - 10;
 p1[2].y = y + 12;
 p1[3].x = x + 10;
 p1[3].y = y + 12;
 p1[4].x = x + 18;
 p1[4].y = y;
 p1[5].x = x + 10;
 p1[5].y = y;
 p1[6].x = x + 10;
 p1[6].y = y - 10;
 p1[7].x = x + 6;
 p1[7].y = y - 10;
 p1[8].x = x + 6;
 p1[8].y = y - 8;

 gdImageSetThickness(im,1);
 gdImageSetAntiAliased(im,couleur2);

 gdImageFilledPolygon(im,p1,9, couleur1);
 gdImagePolygon(im,p1,9, gdAntiAliased);

 *//* canon *//*
 gdImageSetThickness(im,3);
 gdImageLine(im,x-7,y,x-7,y-5,couleur2);
 gdImageLine(im,x-7,y-5,x-12,y-5,couleur2);
 }
 */

static void metflottehasbro(gdImagePtr im, int x, int y, int couleur1,
		int couleur2) {
	gdPoint p1[32], p2[6], p3[4], p4[4], p5[4];
	int i;

	/* gros oeuvre */
	p1[0].x = x - 15;
	p1[0].y = y + 4;
	p1[1].x = x + 16;
	p1[1].y = y + 4;
	p1[2].x = x + 15;
	p1[2].y = y;
	p1[3].x = x + 10;
	p1[3].y = y;
	p1[4].x = x + 10;
	p1[4].y = y - 3;
	p1[5].x = x + 7;
	p1[5].y = y - 3;
	p1[6].x = x + 7;
	p1[6].y = y - 2;
	p1[7].x = x + 4;
	p1[7].y = y - 2;
	p1[8].x = x + 4;
	p1[8].y = y - 9;
	p1[9].x = x + 3;
	p1[9].y = y - 9;
	p1[10].x = x + 3;
	p1[10].y = y - 6;
	p1[11].x = x - 1;
	p1[11].y = y - 6;
	p1[12].x = x - 1;
	p1[12].y = y - 9;
	p1[13].x = x - 2;
	p1[13].y = y - 9;
	p1[14].x = x - 2;
	p1[14].y = y - 13;
	p1[15].x = x - 3;
	p1[15].y = y - 13;
	p1[16].x = x - 3;
	p1[16].y = y - 6;
	p1[17].x = x - 6;
	p1[17].y = y - 6;
	p1[18].x = x - 6;
	p1[18].y = y - 5;
	p1[19].x = x - 3;
	p1[19].y = y - 5;
	p1[20].x = x - 3;
	p1[20].y = y - 4;
	p1[21].x = x - 4;
	p1[21].y = y - 3;
	p1[22].x = x - 4;
	p1[22].y = y - 2;
	p1[23].x = x - 5;
	p1[23].y = y - 2;
	p1[24].x = x - 5;
	p1[24].y = y - 3;
	p1[25].x = x - 9;
	p1[25].y = y - 3;
	p1[26].x = x - 9;
	p1[26].y = y;
	p1[27].x = x - 12;
	p1[27].y = y;
	p1[28].x = x - 12;
	p1[28].y = y - 1;
	p1[29].x = x - 13;
	p1[29].y = y - 1;
	p1[30].x = x - 13;
	p1[30].y = y;
	p1[31].x = x - 12;
	p1[31].y = y;

	gdImageSetThickness(im, 1);
	gdImageSetAntiAliased(im, couleur2);

	gdImageFilledPolygon(im, p1, 32, couleur1);
	gdImagePolygon(im, p1, 32, gdAntiAliased);

	/* petite anse */
	p2[0].x = x + 4;
	p2[0].y = y - 5;
	p2[1].x = x + 7;
	p2[1].y = y - 6;
	p2[2].x = x + 7;
	p2[2].y = y - 3;
	p2[3].x = x + 9;
	p2[3].y = y - 3;
	p2[4].x = x + 9;
	p2[4].y = y - 7;
	p2[5].x = x + 4;
	p2[5].y = y - 6;
	gdImageFilledPolygon(im, p2, 6, couleur1);
	gdImagePolygon(im, p2, 6, gdAntiAliased);

	/* pont */
	gdImageSetThickness(im, 1);
	gdImageLine(im, x - 11, y, x + 13, y, gdAntiAliased);

	/* trois "fenetres" */
	/* gauche */
	p3[0].x = x - 3;
	p3[0].y = y;
	p3[1].x = x - 2;
	p3[1].y = y;
	p3[2].x = x - 2;
	p3[2].y = y - 3;
	p3[3].x = x - 3;
	p3[3].y = y - 3;
	gdImagePolygon(im, p3, 4, gdAntiAliased);

	/* milieu */
	p4[0].x = x - 1;
	p4[0].y = y;
	p4[1].x = x + 1;
	p4[1].y = y;
	p4[2].x = x + 1;
	p4[2].y = y - 3;
	p4[3].x = x - 1;
	p4[3].y = y - 3;
	gdImagePolygon(im, p4, 4, gdAntiAliased);

	/* droite */
	p5[0].x = x + 2;
	p5[0].y = y;
	p5[1].x = x + 3;
	p5[1].y = y;
	p5[2].x = x + 3;
	p5[2].y = y - 3;
	p5[3].x = x + 2;
	p5[3].y = y - 3;
	gdImagePolygon(im, p5, 4, gdAntiAliased);

	/* toit */
	gdImageSetThickness(im, 1);
	gdImageLine(im, x - 4, y - 3, x - 2, y - 5, gdAntiAliased);
	gdImageLine(im, x - 2, y - 5, x - 1, y - 4, gdAntiAliased);
	gdImageLine(im, x - 1, y - 4, x + 1, y - 4, gdAntiAliased);
	gdImageLine(im, x + 1, y - 4, x + 2, y - 5, gdAntiAliased);
	gdImageLine(im, x + 2, y - 5, x + 4, y - 3, gdAntiAliased);

	/* canons */
	gdImageSetThickness(im, 2);
	gdImageLine(im, x - 9, y - 3, x - 10, y - 4, couleur2);
	gdImageLine(im, x + 10, y - 3, x + 12, y - 5, couleur2);

	/* hublots */
	for (i = 0; i < 9; i++)
		gdImageArc(im, x - 11 + 3 * i, y + 2, 1, 1, 0, 360, couleur2);

}

static void metflottedescartes(gdImagePtr im, int x, int y, int couleur1,
		int couleur2) {

	gdPoint p1[5], p2[4], p3[4];

	p1[0].x = p2[0].x = x - 10;
	p1[0].y = p2[0].y = y + 1;

	p1[1].x = p2[1].x = p3[1].x = x + 9;
	p1[1].y = p2[1].y = p3[1].y = y + 2;

	p1[2].x = p3[0].x = x + 14;
	p1[2].y = p3[0].y = y;

	p1[3].x = x + 9;
	p1[3].y = y - 3;

	p1[4].x = x - 8;
	p1[4].y = y - 5;

	p2[2].x = p3[2].x = p1[1].x; /* aligné */
	p2[2].y = p3[2].y = p1[1].y + 5;

	p2[3].x = p1[0].x; /* aligné */
	p2[3].y = p1[0].y + 5;

	p3[3].x = p1[2].x; /* aligné */
	p3[3].y = y + 5;

	gdImageSetThickness(im, 1);
	gdImageSetAntiAliased(im, couleur2);

	gdImageFilledPolygon(im, p1, 5, couleur1);
	gdImagePolygon(im, p1, 5, gdAntiAliased);

	gdImageFilledPolygon(im, p2, 4, couleur1);
	gdImagePolygon(im, p2, 4, gdAntiAliased);

	gdImageFilledPolygon(im, p3, 4, couleur1);
	gdImagePolygon(im, p3, 4, gdAntiAliased);

}

static void metarmee(gdImagePtr im, int x, int y, int couleur1, int couleur2,
		int coultag, char *nom, BOOL croix) {

	if (OPTIOND)
		metarmeedescartes(im, x, y, couleur1, couleur2);
	else if (OPTIONV)
		metarmeevopa(im, x, y, couleur1, TVOPA, 2);
	else
		metarmeehasbro(im, x, y, couleur1, couleur2);

	if (croix)
		metcroix(im, x, y, couleur2);

	if (nom) {
		if (OPTIONC)
			gdImageString(im, gdFontGetTiny(), x + 10, y + 5,
					(unsigned char *) nom, coultag);
		else
			gdImageString(im, gdFontGetMediumBold(), x + 10, y + 5,
					(unsigned char *) nom, coultag);
	}
}

static void metflotte(gdImagePtr im, int x, int y, int couleur1, int couleur2,
		int coultag, char *nom, BOOL croix) {

	if (OPTIOND)
		metflottedescartes(im, x, y, couleur1, couleur2);
	else if (OPTIONV)
		metflottevopa(im, x, y, couleur1, TVOPA, 2);
	else
		metflottehasbro(im, x, y, couleur1, couleur2);

	if (croix)
		metcroix(im, x, y, couleur2);

	if (nom) {
		if (OPTIONC)
			gdImageString(im, gdFontGetTiny(), x + 10, y + 5,
					(unsigned char *) nom, coultag);
		else
			gdImageString(im, gdFontGetMediumBold(), x + 10, y + 5,
					(unsigned char *) nom, coultag);
	}
}

static void metunitedelogee(gdImagePtr im, int type, int couleur1,
		int couleur2, int coultag, char *nom) {
	char buf[TAILLEMESSAGE];
	static int x = 18;
	static int y = 100;
	static BOOL titremis = FALSE;

	if (!titremis) {
		cherchechaine(__FILE__, 13, buf, 0); /*"Unité délogée et son attaquant"*/
		gdImageString(im, gdFontGetMediumBold(), x, y, (unsigned char *) buf,
				coultag);
		titremis = TRUE;
		y += 25;
	}

	switch (type) {
	case ARMEE:
		metarmee(im, x, y, couleur1, couleur2, coultag, nom, FALSE);
		y += 25;
		break;
	case FLOTTE:
		metflotte(im, x, y, couleur1, couleur2, coultag, nom, FALSE);
		y += 25;
		break;
	default:
		assert(FALSE);
	}

}

static void metzoneinterdite(gdImagePtr im, int x, int y, int couleur,
		int couleur2) {
	gdImageSetThickness(im, 3);

	gdImageFilledRectangle(im, x - 4, y - 6, x + 4, y + 6, couleur2);
	gdImageLine(im, x + 4, y + 6, x - 4, y - 6, couleur);
	gdImageLine(im, x + 4, y - 6, x - 4, y + 6, couleur);
}

static void infospreajustements(gdImagePtr im, int col1[], int col2[],
		int coultag) {
	_PAYS **p;
	int nappr, ncent, nunit, najustementsposs;
	static int x = 20;
	static int y = 100;
	int nopays;
	char buf[5];

	cherchechaine(__FILE__, 14, buf, 0); /*"Ajustements attendus"*/
	gdImageString(im, gdFontGetSmall(), x, y, (unsigned char *) buf, coultag);
	y += 25;

	classementpays();

	for (p = PAYSCLASSES.t; p < PAYSCLASSES.t + PAYSCLASSES.n; p++) {

		calculajustements(*p, &ncent, &nunit, &najustementsposs);

		nappr = INF(najustementsposs, ncent - nunit);

		if (nappr == 0)
			continue;

		nopays = (*p) - PAYS.t;
		metdrapeau(im, 10, y, col1[nopays], col2[nopays]);
		sprintf(buf, "%s%d", (nappr > 0 ? "+" : "-"), abs(nappr));
		gdImageString(im, gdFontGetMediumBold(), x, y - 6,
				(unsigned char *) buf, coultag);

		y += 12;
	}
}

static void saison(gdImagePtr im, char *nomsaison, int couleur, int fond) {
	int x, y;

	x = gdImageSX(im) - 6 * strlen(nomsaison) - 5;
	y = 17;

	gdImageFilledRectangle(im, x, y, gdImageSX(im), y + 15, fond);
	gdImageString(im, gdFontGetSmall(), x + 2, y, (unsigned char *) nomsaison,
			couleur);
}

static void datelimite(gdImagePtr im, char *dl, int couleur, int fond) {
	int x, y;

	x = gdImageSX(im) - 6 * strlen(dl) - 5;
	y = 30;

	gdImageFilledRectangle(im, x, y, gdImageSX(im), y + 15, fond);
	gdImageString(im, gdFontGetSmall(), x + 2, y, (unsigned char *) dl, couleur);
}

static void partie(gdImagePtr im, char *nompartie, int couleur) {
	int x, y;

	x = 200;
	y = 1;

	gdImageString(im, gdFontGetGiant(), x, y, (unsigned char *) nompartie,
			couleur);
}

static void titre1(gdImagePtr im, char *libelle, int couleur) {
	int x, y;

	x = 200;
	y = 17;

	gdImageString(im, gdFontGetSmall(), x, y, (unsigned char *) libelle,
			couleur);
}

static void titre2(gdImagePtr im, char *libelle, int couleur) {
	int x, y;

	x = 200;
	y = 32;

	gdImageString(im, gdFontGetSmall(), x, y, (unsigned char *) libelle,
			couleur);
}

static void gdate(gdImagePtr im, int couleur) {
	time_t t;
	struct tm temps;
	char *p, d[100];
	int x, y;

	x = 5;
	y = gdImageSY(im) - 10;

	strcpy(d, "GMT ");

	time(&t);
	temps = *gmtime(&t);
	strcat(d, asctime(&temps));

	/* Remplace le retour chariot par fin chaine */
	for (p = d; *p != '\n'; p++)
		;
	*p = '\0';

	gdImageString(im, gdFontGetTiny(), x, y, (unsigned char *) d, couleur);
}

static void cr(gdImagePtr im, char *auteur, int couleur) {
	int x, y;

	x = gdImageSX(im) - 6 * strlen(auteur) - 2;
	y = gdImageSY(im) - 10;

	gdImageString(im, gdFontGetTiny(), x, y, (unsigned char *) auteur, couleur);
}

static void legende(gdImagePtr im, int col1[], int col2[], char *nomficjoueurs,
		int face, int fond) {
	int i, y, xl, yl;
	int ncentres, nunites, dummy, nopays;
	char *p, *q, buf[TLEGENDE], nomjoueur[NPAYS][TJOUEUR], nompays[TJOUEUR];
	FILE *fd = NULL;
	_PAYS *pays;

	xl = 195;
	yl = 95;

	gdImageFilledRectangle(im, 0, 0, xl, yl, fond);
	gdImageRectangle(im, 0, 0, xl, yl, face);

	assert(NPAYS < NPAYSS);

	for (i = 0; i < NPAYS; i++)
		strcpy(nomjoueur[i], "");

	/* Si echec sans gravite on fera comme si le parametre existe pas */
	if ((fd = fopen(nomficjoueurs, "rt")) != NULL) {

		for (;;) {

			if (!fgets(buf, TLEGENDE - 1, fd))
				break;

			/* Nom du pays */
			q = nompays;
			p = buf;
			for (; *p != ' ' && *p != '\t' && *p != '\n' && *p != EOS; p++, q++)
				*q = *p;
			*q = EOS;

			for (pays = PAYS.t, nopays = 0; pays < PAYS.t + PAYS.n; pays++, nopays++)
				if (!strcmp(pays->nom, nompays))
					break;
			if (pays == PAYS.t + PAYS.n)
				break;

			/* passe espaces et tabulations */
			for (; *p == ' ' || *p == '\t'; p++)
				;

			/* Nom du joueur */
			q = nomjoueur[nopays];
			for (; *p != '\n' && *p != EOS; p++, q++)
				*q = *p;
			*q = EOS;

		}
	}

	for (i = 0; i < NPAYS; i++) {

		y = 13 * i;
		metdrapeau(im, 10, y + 7, col1[i], col2[i]);
		calculajustements(PAYS.t + i, &ncentres, &nunites, &dummy);

		sprintf(buf, "%-10.10s", PAYS.t[i].nom);
		gdImageString(im, gdFontGetTiny(), 22, y + 4, (unsigned char *) buf,
				face);

		sprintf(buf, "%2dc", ncentres);
		gdImageString(im, gdFontGetSmall(), 74, y, (unsigned char *) buf, face);

		sprintf(buf, "%2du", nunites);
		gdImageString(im, gdFontGetSmall(), 96, y, (unsigned char *) buf, face);

		sprintf(buf, "%-15.15s", nomjoueur[i]);
		gdImageString(im, gdFontGetTiny(), 118, y + 4, (unsigned char *) buf,
				face);
	}

	if (fd)
		fclose(fd);
}

static void localisecentre(_CENTRE *centre, int *x, int *y) {
	char buf[TAILLEMESSAGE * 2];
	_CENTREGEO *t;

	for (t = CENTREGEO.t; t < CENTREGEO.t + CENTREGEO.n; t++)
		if (t->centre == centre) {
			*x = t->x;
			*y = t->y;
			return;
		}

	cherchechaine(__FILE__, 1, buf, 1, centre->region->nom); /*"Impossible de localiser le centre %1"*/
	erreurparse(NULL, LACARTE, FALSE, buf);
}

static void localisezone(_ZONE *zone, int *x, int *y) {
	char buf[TAILLEMESSAGE * 2], nomzone[TAILLEMOT * 2];
	_ZONEGEO *t;

	for (t = ZONEGEO.t; t < ZONEGEO.t + ZONEGEO.n; t++)
		if (t->zone == zone) {
			*x = t->x;
			*y = t->y;
			return;
		}

	strcpy(nomzone, zone->region->nom);
	strcat(nomzone, zone->specificite);
	cherchechaine(__FILE__, 2, buf, 1, nomzone); /*"Impossible de localiser la zone %1"*/
	erreurparse(NULL, LACARTE, FALSE, buf);
}

static void localiseregion(_REGION *region, int *x, int *y) {
	char buf[TAILLEMESSAGE * 2], nomregion[TAILLEMOT * 2];
	_ZONEGEO *t;

	for (t = ZONEGEO.t; t < ZONEGEO.t + ZONEGEO.n; t++)

		if (t->zone->region == region && !strcmp(t->zone->specificite, "")) {
			*x = t->x;
			*y = t->y;
			return;
		}

	strcpy(nomregion, region->nom);
	cherchechaine(__FILE__, 3, buf, 11, nomregion); /*"Impossible de localiser la region %1"*/
	erreurparse(NULL, LACARTE, FALSE, buf);
}

static int trouvecouleur(gdImagePtr im, int r, int g, int b, const char *nom) {
	char buf[TAILLEMESSAGE * 2];
	int vict, coul;

	/*  printf("cherche rgb= %d %d %d...",r,g,b); */

	/* La couleur existe deja dans la palette */
	if ((coul = gdImageColorExact(im, r, g, b)) != -1) {
		/*           printf("exacte a %d\n",coul); */
		return coul;
	}

	/* Une entree libre existe dans la palette */
	if ((coul = gdImageColorAllocate(im, r, g, b)) != -1) {
		/*           printf("allouee a %d\n",coul); */
		return coul;
	}

	/* On va prendre une couleur proche de la palette et la detourner */
	vict = gdImageColorClosest(im, r, g, b);
	gdImageColorDeallocate(im, vict);

	if ((coul = gdImageColorAllocate(im, r, g, b)) == -1) {
		cherchechaine(__FILE__, 12, buf, 1, nom); /*"Impossible d'allouer la couleur %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	/*  printf("victime a %d\n", coul); */
	return coul;
}

static void allouecouleur(gdImagePtr im, int *coul1, int *coul2, int r, int g,
		int b, const char *nom1, const char *nom2) {
	int r2, g2, b2;

	*coul1 = trouvecouleur(im, r, g, b, nom1);

	if (coul2 == NULL)
		return;

	r2 = g2 = b2 = 0;
	/* Si c'est très sombre */
	if (r < 255 / 4 && g < 255 / 4 && b < 255 / 4) {
		r2 = g2 = b2 = 255 / 3;
	}

	*coul2 = trouvecouleur(im, r2, g2, b2, nom2);

}

static _COULEUR *cherchecouleur(_PAYS *pays) {
	_COULEUR *p;

	for (p = COULEUR.t; p < COULEUR.t + COULEUR.n; p++)
		if (p->pays == pays)
			return p;

	return NULL;
}

static int calculehauteurtexte(gdImagePtr im, int *lcol, int *nlig, int *htexte) {
	FILE *fd;
	int largeurmaxi, nblignes, ncol;
	int L;
	char *p, ordre[TORDRE];

	/* Si echec sans gravite on fera comme si le parametre existe pas */
	if ((fd = fopen(NOMFICORDRES, "rt")) == NULL)
		return FALSE;
	largeurmaxi = 0;
	nblignes = 0;
	for (;;) {
		if (!fgets(ordre, TJOUEUR - 1, fd))
			break;
		/* Retire le '\n' final */
		for (p = ordre; *p != '\n' && *p != '\0'; p++)
			;
		if (*p == '\n')
			*p = '\0';
		/* Filtre les '\t' en ' ' */
		for (p = ordre; *p != '\0'; p++)
			if (*p == '\t')
				*p = ' ';
		if (((signed) strlen(ordre)) > largeurmaxi)
			largeurmaxi = strlen(ordre);
		nblignes++;
	}
	fclose(fd);

	/* calculs des dimensions de la fenetre */
	L = (gdImageSX(im) - 2 * mx) / ratiox;

	/* calcul de la largeur des colonnes */
	ncol = L / (largeurmaxi + 1);
	if (ncol == 0)
		return FALSE;
	*lcol = L / ncol;

	/* calcul du nombre de lignes par colonne */
	(*nlig) = 0;
	while (((*nlig) * ncol) < nblignes)
		(*nlig)++;

	assert(*lcol >= largeurmaxi);
	assert(nblignes <= ncol * (*nlig));

	*htexte = (*nlig) * ratioy + 2 * my;
	return TRUE;
}

static void remplittexte(gdImagePtr im, int lcol, int nlig, int face, int fond) {
	FILE *fd;
	int lig, col, x, y;
	char *p, ordre[TORDRE];

	gdImageFilledRectangle(im, 0, 0, gdImageSX(im), gdImageSY(im), fond);
	gdImageRectangle(im, 1, 1, gdImageSX(im) - 2, gdImageSY(im) - 2, face);

	if ((fd = fopen(NOMFICORDRES, "r")) == NULL)
		return;

	lig = col = 0;
	for (;;) {
		if (!fgets(ordre, TJOUEUR - 1, fd))
			break;
		/* Retire le '\n' (et le '13' sous unix) final */
		for (p = ordre; *p != '\n' && *p != 13 && *p != '\0'; p++)
			;
		if (*p == '\n' || *p == 13)
			*p = '\0';
		/* Filtre les '\t' en ' ' */
		for (p = ordre; *p != '\0'; p++)
			if (*p == '\t')
				*p = ' ';

		x = mx + col * lcol * ratiox;
		y = my + lig * ratioy;
		/* Copie vers la fenetre */
		gdImageString(im, gdFontGetMediumBold(), x, y, (unsigned char *) ordre,
				face);
		lig++;
		if (lig > nlig - 1) {
			lig = 0;
			col++;
		}
	}
	fclose(fd);
}

static void inseretag(gdImagePtr im, char *libelle, int col) {
	double angle, cos_angle, sin_angle;
	int hauteurtexte, largeurtexte, largeurdiago, x, y;

	gdImageStringFT(NULL, &brect[0], col, fontevariable, 40, 0.0, 0, 0, libelle);

	largeurtexte = brect[2] - brect[0];
	hauteurtexte = brect[1] - brect[7];

	largeurdiago = sqrt((double) (gdImageSX(im) * gdImageSX(im) + gdImageSY(im) * gdImageSY(im)));

	cos_angle = ((double) gdImageSX(im)) / largeurdiago;
	sin_angle = ((double) gdImageSY(im)) / largeurdiago;

	/* centre */
	x = gdImageSX(im) / 2;
	y = gdImageSY(im) / 2;

	/* decalage largeur texte */
	x -= (int) (cos_angle * ((float) largeurtexte) / 2.0);
	y += (int) (sin_angle * ((float) largeurtexte) / 2.0);

	/* decalage hauteur texte */
	x += (int) (sin_angle * ((float) hauteurtexte) / 2.0);
	y += (int) (cos_angle * ((float) hauteurtexte) / 2.0);

	angle = atan(((double) gdImageSY(im)) / ((double) gdImageSX(im)));
	gdImageStringFT(im, &brect[0], col, fontevariable, 40, angle, x, y, libelle);
}

static BOOL partiegagnee(void) {
	_POSSESSION *p;
	_PAYS *s;
	int ncentres;

	for (s = PAYS.t; s < PAYS.t + PAYS.n; s++) {
		ncentres = 0;
		for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++)
			if (p->pays == s)
				ncentres++;
		if (ncentres > (CENTRE.n / 2))
			return TRUE;
	}

	return FALSE;
}

void decritgraphique(char *nompartie, char *nomsaison, char *dl,
		char *libelle1, char *libelle2, char *nomficjoueurs, char *auteur) {
	_ZONE *p;
	_CENTRE *q;
	_POSSESSION *s;
	_UNITE *t;
	_INTERDIT *u;
	_DELOGEE *v;
	int x, y;
	char cartesource[TAILLENOMFIC];
	char tag[TAILLEMOT];
	char nom[TAILLEMOT];
	char buf[TAILLEMESSAGE * 2];
	char nomcoul1[TAILLEMESSAGE], nomcoul2[TAILLEMESSAGE];
	int i;
	int idpays;
	int GAGNEE;
	_PAYS *pays;
	int coulir, coultag;
	int htexte;
	_COULEUR *couleur;
	_CODE *code;

	gdImagePtr im_complete, im_carte, im_ordres;

	int col1[NPAYS], col2[NPAYS], fondlegende, facelegende;

	FILE *pngin, *pngout;
	int faceordres, fondordres;
	int lcol, nlig;

	int facecr;

	(void) sprintf(cartesource, "CARTE.PNG");
	addpath(cartesource, FALSE);

	if ((pngin = fopen(cartesource, "rb")) == NULL) {
		cherchechaine(__FILE__, 4, buf, 1, cartesource); /*"Impossible ouvrir fichier image lecture %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	if ((im_carte = gdImageCreateFromPng(pngin)) == NULL) {
		cherchechaine(__FILE__, 5, buf, 0); /*"Impossible creer image"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

    htexte = 0; /* evite un avertissement */
	im_ordres = NULL;
	if (strcmp(NOMFICORDRES, "")) {

		if (calculehauteurtexte(im_carte, &lcol, &nlig, &htexte)) {

			if ((im_ordres = gdImageCreate(gdImageSX(im_carte), htexte)) == NULL) {
				cherchechaine(__FILE__, 9, buf, 0); /*"Impossible creer image"*/
				erreur(NULL, ERRSYSTEME, buf);
			}

			allouecouleur(im_ordres, &fondordres, &faceordres, 255, 255, 255,
					"blanche legende", "noir ecriture");
			remplittexte(im_ordres, lcol, nlig, faceordres, fondordres);

		}
	}

	allouecouleur(im_carte, &facecr, NULL, 0, 0, 0, "blanc copyright", "non");
	gdate(im_carte, facecr);
	cr(im_carte, auteur, facecr);

	if (im_ordres != NULL) {

		if ((im_complete = gdImageCreate(gdImageSX(im_carte), gdImageSY(im_carte) + htexte)) == NULL) {
			cherchechaine(__FILE__, 10, buf, 0); /*"Impossible creer image"*/
			erreur(NULL, ERRSYSTEME, buf);
		}

		gdImageCopy(im_complete, im_carte, 0, 0, 0, 0, gdImageSX(im_carte), gdImageSY(im_carte));
		gdImageCopy(im_complete, im_ordres, 0, gdImageSY(im_carte), 0, 0, gdImageSX(im_ordres), gdImageSY(im_ordres));
		gdImageDestroy(im_carte);
		gdImageDestroy(im_ordres);

	} else {

		if ((im_complete = gdImageCreate(gdImageSX(im_carte), gdImageSY(im_carte))) == NULL) {
			cherchechaine(__FILE__, 10, buf, 0); /*"Impossible creer image"*/
			erreur(NULL, ERRSYSTEME, buf);
		}

		gdImageCopy(im_complete, im_carte, 0, 0, 0, 0, gdImageSX(im_carte), gdImageSY(im_carte));
		gdImageDestroy(im_carte);

	}

	allouecouleur(im_complete, &fondlegende, &facelegende, 255, 255, 255,
			"blanche legende", "noir ecriture");

	for (pays = PAYS.t, i = 0; pays < PAYS.t + PAYS.n; pays++, i++) {
		if ((couleur = cherchecouleur(pays)) == NULL) {
			cherchechaine(__FILE__, 8, buf, 1, pays->nom); /*"Impossible trouver couleur pour %1"*/
			erreur(NULL, ERRSYSTEME, buf);
		}
		sprintf(nomcoul1, "Pays %s : couleur des objets", pays->nom);
		sprintf(nomcoul2, "Pays %s : couleur des contours", pays->nom);
		allouecouleur(im_complete, &col1[i], &col2[i], couleur->red,
				couleur->green, couleur->blue, nomcoul1, nomcoul2);
	}

	allouecouleur(im_complete, &coultag, NULL, 255, 0, 0, "rouge tag",
			"inutile");

	if (OPTIONV) {
		for (i = 0; i < NPAYS; i++)
			colvopa[i] = col1[i];
		noirvopa = facelegende;
		blancvopa = fondlegende;
	}

	gdImageSetThickness(im_complete, 1);

	partie(im_complete, nompartie, coultag);
	saison(im_complete, nomsaison, coultag, fondlegende);
	datelimite(im_complete, dl, coultag, fondlegende);
	titre1(im_complete, libelle1, facelegende);
	titre2(im_complete, libelle2, facelegende);
	if (!OPTIONl)
		legende(im_complete, col1, col2, nomficjoueurs, facelegende,
				fondlegende);

	/* On met les trigrammes */
	for (code = CODE.t; code < CODE.t + CODE.n; code++) {
		x = code->x;
		y = code->y;
		x -= 12;
		y -= 8;
		strcpy(tag, code->nom);
		if(code->majuscules)
		Strupr(tag);
		else
		Strlwr(tag); 
		gdImageString(im_complete,gdFontGetSmall(),x,y,(unsigned char *) tag,coultag);
	}

	if (OPTIONC) {

		idpays = 1;

		for (q = CENTRE.t; q < CENTRE.t + CENTRE.n; q++) {
			x = y = 0; /* evite un avertissement */
			localisecentre(q, &x, &y);
			idpays++;
			idpays %= NPAYS;
			sprintf(nom, "%s", q->region->nom);
			metcentre(im_complete, x, y, col1[idpays], col2[idpays],
					facelegende, nom, TRUE);
		}

		for (p = ZONE.t; p < ZONE.t + ZONE.n; p++) {
			x = y = 0; /* evite un avertissement */
			localisezone(p, &x, &y);
			idpays++;
			idpays %= NPAYS;
			switch (p->typezone) {
			case TERRE:
				sprintf(nom, "%s%s", p->region->nom, p->specificite);
				metarmee(im_complete, x, y, col1[idpays], col2[idpays],
						facelegende, nom, FALSE);
				break;
			case COTE:
				sprintf(nom, "%s%s", p->region->nom, p->specificite);
				if (strcmp(p->specificite, ""))
					metflotte(im_complete, x, y, col1[idpays], col2[idpays],
							facelegende, nom, FALSE);
				else {
					metarmee(im_complete, x, y, col1[idpays], col2[idpays],
							facelegende, nom, FALSE);
					metflotte(im_complete, x, y, col1[idpays], col2[idpays],
							facelegende, nom, FALSE);
				}
				break;
			case MER:
				sprintf(nom, "%s%s", p->region->nom, p->specificite);
				metflotte(im_complete, x, y, col1[idpays], col2[idpays],
						facelegende, nom, FALSE);
				break;
			default:
				assert(FALSE);
			}
		}

	} else {

		for (s = POSSESSION.t; s < POSSESSION.t + POSSESSION.n; s++) {
			x = y = 0; /* evite un avertissement */
			localisecentre(s->centre, &x, &y);
			if (OPTIONN)
				strncpy(tag, s->pays->nom, 3);
			metcentre(im_complete, x, y, col1[vpays(s->pays)], col2[vpays(
					s->pays)], facelegende, OPTIONN ? tag : NULL, FALSE);
		}

		for (t = UNITE.t; t < UNITE.t + UNITE.n; t++) {

			/* On affiche a part les delogees */
			if (unitedelogee(t))
				continue;

			x = y = 0; /* evite un avertissement */
			localisezone(t->zone, &x, &y);
			switch (t->typeunite) {
			case ARMEE:
				if (OPTIONN)
					strncpy(tag, t->pays->nom, 3);
				metarmee(im_complete, x, y, col1[vpays(t->pays)], col2[vpays(
						t->pays)], facelegende, OPTIONN ? tag : NULL, FALSE);
				break;
			case FLOTTE:
				if (OPTIONN)
					strncpy(tag, t->pays->nom, 3);
				metflotte(im_complete, x, y, col1[vpays(t->pays)], col2[vpays(
						t->pays)], facelegende, OPTIONN ? tag : NULL, FALSE);
				break;
			default:
				assert(FALSE);
			}
		}

		allouecouleur(im_complete, &coulir, NULL, 255, 0, 0,
				"rouge interdiretraite", "inutile");
		for (u = INTERDIT.t; u < INTERDIT.t + INTERDIT.n; u++) {

			x = y = 0; /* evite un avertissement */
			localiseregion(u->region, &x, &y);
			metzoneinterdite(im_complete, x, y, coulir, fondlegende);
		}

		for (v = DELOGEE.t; v < DELOGEE.t + DELOGEE.n; v++) {

			cherchechaine(__FILE__, 16, buf, 0); /*"depuis"*/
			sprintf(tag, "%s%s (%s %s%s)", v->unite->zone->region->nom,
					v->unite->zone->specificite, buf, v->zoneorig->region->nom,
					v->zoneorig->specificite);

			metunitedelogee(im_complete, v->unite->typeunite, col1[vpays(
					v->unite->pays)], col2[vpays(v->unite->pays)], facelegende,
					tag);
		}

	}

	GAGNEE = partiegagnee();

	if ((!GAGNEE) && (IDSAISON) (SAISON % 5) == BILAN)
		infospreajustements(im_complete, col1, col2, facelegende);

	if (GAGNEE) {
		cherchechaine(__FILE__, 17, buf, 0); /*"Partie gagnee"*/
		inseretag(im_complete, buf, coultag);
	}

	if ((pngout = fopen(NOMFICGRAPHIQUE, "wb")) == NULL) {
		cherchechaine(__FILE__, 6, buf, 1, NOMFICGRAPHIQUE); /*"Impossible ouvrir fichier image ecriture %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	/* On conserve les effets alpha */
	/* gdImageSaveAlpha(im,1); */

	/* Effet entrelacement decoratif */
	gdImageInterlace(im_complete, 1);

	/* 0 = Pas de compression */
	/* 9 = Compression maximum */
	gdImagePngEx(im_complete, pngout, 9);

	fclose(pngout);

	gdImageDestroy(im_complete);

}

void decrithtml(void) {
	_ZONE *p;
	_ARMEEVOISIN *q;
	_FLOTTEVOISIN *r;
	_UNITE *u;
	_DELOGEE *v;
	_PAYS **pp;
	int nappr, ncent, nunit, najustementsposs;
	int nopays;
	BOOL prem;
	int x, y, rayon;
	char texte[TAILLEMESSAGE];
	FILE *htmout;
	char buf[TAILLEMESSAGE * 2];
	int xd = 18;
	int yd = 100;
	int xa = 18;
	int ya = 112;

	if ((htmout = fopen(NOMFICHTML, "wt")) == NULL) {
		cherchechaine(__FILE__, 15, buf, 1, NOMFICHTML); /*"Impossible ouvrir fichier html ecriture %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	fprintf(htmout, "<map  name='map1'>\n");
	rayon = 20;
	for (p = ZONE.t; p < ZONE.t + ZONE.n; p++) {
		u = chercheoccupantnondeloge(p->region);
		if (u == NULL || u->zone != p) { /* vide ou unite sur la meme region differente zone */
			sprintf(texte, "%s%s => ", p->region->nom, p->specificite);
			if (p->typezone == TERRE || p->typezone == COTE) {
				strcat(texte, "A : ");
				prem = TRUE;
				for (q = ARMEEVOISIN.t; q < ARMEEVOISIN.t + ARMEEVOISIN.n; q++)
					if (q->zone1 == p) {
						if (!prem)
							strcat(texte, ", ");
						prem = FALSE;
						strcat(texte, q->zone2->region->nom);
						strcat(texte, q->zone2->specificite);
					}
				strcat(texte, ".");
			}
			if (p->typezone == COTE)
				strcat(texte, " ");
			if (p->typezone == MER || p->typezone == COTE) {
				strcat(texte, "F : ");
				prem = TRUE;
				for (r = FLOTTEVOISIN.t; r < FLOTTEVOISIN.t + FLOTTEVOISIN.n; r++)
					if (r->zone1 == p) {
						if (!prem)
							strcat(texte, ", ");
						prem = FALSE;
						strcat(texte, r->zone2->region->nom);
						strcat(texte, r->zone2->specificite);
					}
				strcat(texte, ".");
			}
		} else { /* occupee */
			sprintf(texte, "%s %s %s%s => ", u->pays->adjectif, (u->typeunite
					== ARMEE ? "A" : "F"), u->zone->region->nom,
					u->zone->specificite);
			switch (u->typeunite) {
			case ARMEE:
				strcat(texte, " ");
				prem = TRUE;
				for (q = ARMEEVOISIN.t; q < ARMEEVOISIN.t + ARMEEVOISIN.n; q++)
					if (q->zone1 == p) {
						if (!prem)
							strcat(texte, ", ");
						prem = FALSE;
						strcat(texte, q->zone2->region->nom);
						strcat(texte, q->zone2->specificite);
					}
				strcat(texte, ".");
				break;
			case FLOTTE:
				strcat(texte, " ");
				prem = TRUE;
				for (r = FLOTTEVOISIN.t; r < FLOTTEVOISIN.t + FLOTTEVOISIN.n; r++)
					if (r->zone1 == p) {
						if (!prem)
							strcat(texte, ", ");
						prem = FALSE;
						strcat(texte, r->zone2->region->nom);
						strcat(texte, r->zone2->specificite);
					}
				strcat(texte, ".");
				break;
			}
		}
		x = y = 0; /* evite avertissement */
		localisezone(p, &x, &y);
		fprintf(htmout,
				"<area shape='circle' coords='%d,%d,%d' title='%s' alt='' />\n",
				x, y, rayon, texte);
	}

	for (v = DELOGEE.t; v < DELOGEE.t + DELOGEE.n; v++) {

		sprintf(texte, "%s %s %s%s (r)=> ", v->unite->pays->adjectif,
				(v->unite->typeunite == ARMEE ? "A" : "F"),
				v->unite->zone->region->nom, v->unite->zone->specificite);
		switch (v->unite->typeunite) {
		case ARMEE:
			strcat(texte, " ");
			prem = TRUE;
			for (q = ARMEEVOISIN.t; q < ARMEEVOISIN.t + ARMEEVOISIN.n; q++)
				/* marche aussi avec la fonction chercheoccupant() */
				if (q->zone1 == v->unite->zone && !chercheoccupantnondeloge(
						q->zone2->region)
						&& !interditretraite(q->zone2->region)
						&& q->zone2->region != v->zoneorig->region) {
					if (!prem)
						strcat(texte, ", ");
					prem = FALSE;
					strcat(texte, q->zone2->region->nom);
					strcat(texte, q->zone2->specificite);
				}
			strcat(texte, ".");
			break;
		case FLOTTE:
			strcat(texte, " ");
			prem = TRUE;
			for (r = FLOTTEVOISIN.t; r < FLOTTEVOISIN.t + FLOTTEVOISIN.n; r++)
				/* marche aussi avec la fonction chercheoccupant() */
				if (r->zone1 == v->unite->zone && !chercheoccupantnondeloge(
						r->zone2->region)
						&& !interditretraite(r->zone2->region)
						&& r->zone2->region != v->zoneorig->region) {
					if (!prem)
						strcat(texte, ", ");
					prem = FALSE;
					strcat(texte, r->zone2->region->nom);
					strcat(texte, r->zone2->specificite);
				}
			strcat(texte, ".");
			break;
		}
		yd += 25;
		fprintf(htmout,
				"<area shape='circle' coords='%d,%d,%d' title='%s' alt='' />\n",
				xd, yd, rayon, texte);
	}

	for (pp = PAYSCLASSES.t; pp < PAYSCLASSES.t + PAYSCLASSES.n; pp++) {

		calculajustements(*pp, &ncent, &nunit, &najustementsposs);

		nappr = INF(najustementsposs, ncent - nunit);

		if (nappr == 0)
			continue;

		nopays = (*pp) - PAYS.t;
		if(nappr > 0) {
		  cherchechaine(__FILE__, 18, buf, 0,NOMFICGRAPHIQUE); /*"peut construire "*/
		  sprintf(texte,"%s %s %d",(*pp)->nom,buf,nappr);
		  fprintf(htmout,
				"<area shape='circle' coords='%d,%d,%d' title='%s' alt='' />\n",
				xa, ya, rayon, texte);
		} else {
  		  cherchechaine(__FILE__, 19, buf, 0,NOMFICGRAPHIQUE); /*"doit retirer "*/
		  sprintf(texte,"%s %s %d",(*pp)->nom,buf,abs(nappr));
		  fprintf(htmout,
				"<area shape='circle' coords='%d,%d,%d' title='%s' alt='' />\n",
				xa, ya, rayon, texte);
		}

		ya += 12;
	}
	
	
	fprintf(htmout, "</map>\n");

	fclose(htmout);
}
