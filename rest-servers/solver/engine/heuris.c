#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

#define INFINITE 2147483647

typedef/**/ LISTE(_ZONE *, NZONES) _CHAINEZONES;

static BOOL armeevoisinetendu(_ZONE *, _ZONE *);
static int calculeloignement(TYPEUNITE, _ZONE *, _PAYS *);

static BOOL armeevoisinetendu(_ZONE *zone1, _ZONE *zone2) {
	_ZONE *q, *r;

	for (q = ZONE.t; q < ZONE.t + ZONE.n - 1; q++)
		for (r = q + 1; r < ZONE.t + ZONE.n; r++)

			if ((q->region == zone1->region && r->region == zone2->region)
					|| (q->region == zone2->region && r->region
							== zone1->region)) {

				if (flottevoisin(q, r))
					return TRUE;

				if (armeevoisin(q, r))
					return TRUE;
			}

	return FALSE;
}

static int calculeloignement(TYPEUNITE typeunite, _ZONE *zone, _PAYS *pays)
/* La distance est exprimee en voisins a traverser pour deux unites
 sur des zones des centres, que ce soit par flotte ou par armee */
{
	_ZONE **s, *p, *r;
	_CENTREDEPART *q;
	_CHAINEZONES CHAINE1, CHAINE2, CHAINE3;
	int dist;

	/* A -t- on trouve un centre de depart du pays ? */
	for (q = CENTREDEPART.t; q < CENTREDEPART.t + CENTREDEPART.n; q++)
		if (q->pays == pays && q->centre->region == zone->region)
			return 0;

	CHAINE1.n = 0; /* Les anciens */

	CHAINE2.n = 0; /* Les nouveaux */
	CHAINE2.t[CHAINE2.n++] = zone;

	dist = 0;
	for (;;) {

		CHAINE3.n = 0;
		for (p = ZONE.t; p < ZONE.t + ZONE.n; p++) { /* Etude de la region p : */

			for (s = CHAINE1.t; s < CHAINE1.t + CHAINE1.n; s++)
				if (*s == p)
					break;
			if (s < CHAINE1.t + CHAINE1.n) /* deja dans la chaine des anciens */
				continue;

			for (s = CHAINE2.t; s < CHAINE2.t + CHAINE2.n; s++)
				if (*s == p)
					break;
			if (s < CHAINE2.t + CHAINE2.n) /* deja dans la chaine des nouveaux */
				continue;

			/* Est-il voisin d'un nouveau ? */
			for (s = CHAINE2.t; s < CHAINE2.t + CHAINE2.n; s++) {
				for (r = ZONE.t; r < ZONE.t + ZONE.n; r++)
					if (r == *s)
						break;
				assert(r != ZONE.t + ZONE.n);
				if ((typeunite == ARMEE && armeevoisinetendu(*s, p))
						|| (typeunite == FLOTTE && flottevoisin(*s, p)))
					break;
			}

			if (s == CHAINE2.t + CHAINE2.n)
				continue;

			CHAINE3.t[CHAINE3.n++] = p; /* Voisin d'un nouveau :  mis dasn CHAINE3*/
		}

		/* Si c'est une flotte en terre */
		if (CHAINE2.n == 0)
			return INFINITE;

		/* Les nouveaux passent dans les anciens */
		for (s = CHAINE2.t; s < CHAINE2.t + CHAINE2.n; s++)
			CHAINE1.t[CHAINE1.n++] = *s;

		/* CHAINE3 remplace les nouveaux */
		CHAINE2.n = 0;
		for (s = CHAINE3.t; s < CHAINE3.t + CHAINE3.n; s++)
			CHAINE2.t[CHAINE2.n++] = *s;

		/* A -t- on trouve un centre de depart du pays ? */
		for (q = CENTREDEPART.t; q < CENTREDEPART.t + CENTREDEPART.n; q++) {

			if (q->pays != pays)
				continue;

			for (s = CHAINE1.t; s < CHAINE1.t + CHAINE1.n; s++)
				if ((*s)->region == q->centre->region)
					break;
			if (s < CHAINE1.t + CHAINE1.n) /* Trouve */
				return dist;
		}

		dist++;

	} /* boucle infinie */
}

void calculeeloignements(void) {
	_ZONE *zon;
	_PAYS *pay;
	char buf[TAILLEMESSAGE];
	TYPEUNITE typeunite;
	int val;

	/* Calcul des eloignements eux-meme */
	for (pay = PAYS.t; pay < PAYS.t + PAYS.n; pay++) {
		(void) printf(";------------\n; %s\n;------------\n", pay->nom);
		for (typeunite = FLOTTE; typeunite <= ARMEE; typeunite++) {
			for (zon = ZONE.t; zon < ZONE.t + ZONE.n; zon++)
				if ((val = calculeloignement(typeunite, zon, pay)) != INFINITE)
					(void) printf("ELOIGNEMENT %s %s  %s%s  %d\n", (typeunite
							== FLOTTE ? "F" : "A"), pay->nom, zon->region->nom,
							zon->specificite, val);
			(void) printf("\n");
		}
		cherchechaine(__FILE__, 4, buf, 1, pay->nom); /*"Fin calculs pour %1"*/
		(void) fprintf(stderr, "%s\n", buf);
	}
}

void verifiecarte(void) {
	_FLOTTEVOISIN *fv;
	_ARMEEVOISIN *av;
	BOOL probleme;
	char buf[TAILLEMESSAGE];

	probleme = FALSE;
	for (fv = FLOTTEVOISIN.t; fv < FLOTTEVOISIN.t + FLOTTEVOISIN.n; fv++) {
		if (fv->zone1 == fv->zone2) {
			cherchechaine(__FILE__, 5, buf, 2, fv->zone1->region->nom,
					fv->zone1->specificite); /*"%1%2 est voisin par flotte avec lui-meme !"*/
			avertir(buf);
			probleme = TRUE;
		}
		if (!compatibles(FLOTTE, fv->zone1) || !compatibles(FLOTTE, fv->zone2)) {
			cherchechaine(__FILE__, 6, buf, 4, fv->zone1->region->nom,
					fv->zone1->specificite, fv->zone2->region->nom,
					fv->zone2->specificite); /*"%1%2 et %3%4 sont voisins par flotte !"*/
			avertir(buf);
			probleme = TRUE;
		}
		if (!flottevoisin(fv->zone2, fv->zone1)) {
			cherchechaine(__FILE__, 7, buf, 4, fv->zone1->region->nom,
					fv->zone1->specificite, fv->zone2->region->nom,
					fv->zone2->specificite); /*"%1%2 est voisin par flotte de %3%4  mais pas l'oppose !"*/
			avertir(buf);
			probleme = TRUE;
		}
	}
	for (av = ARMEEVOISIN.t; av < ARMEEVOISIN.t + ARMEEVOISIN.n; av++) {
		if (av->zone1 == av->zone2) {
			cherchechaine(__FILE__, 8, buf, 2, av->zone1->region->nom,
					av->zone1->specificite); /*"%1%2 est voisin par armee avec lui-meme !"*/
			avertir(buf);
			probleme = TRUE;
		}
		if (!compatibles(ARMEE, av->zone1) || !compatibles(ARMEE, av->zone2)) {
			cherchechaine(__FILE__, 9, buf, 4, av->zone1->region->nom,
					av->zone1->specificite, av->zone2->region->nom,
					av->zone2->specificite); /*"%1%2 et %3%4 sont voisins par armee !"*/
			avertir(buf);
			probleme = TRUE;
		}
		if (!armeevoisin(av->zone2, av->zone1)) {
			cherchechaine(__FILE__, 10, buf, 4, av->zone1->region->nom,
					av->zone1->specificite, av->zone2->region->nom,
					av->zone2->specificite); /*"%1%2 est voisin par armee de %3%4  mais pas l'oppose !"*/
			avertir(buf);
			probleme = TRUE;
		}
	}
	if (!probleme) {
		cherchechaine(__FILE__, 11, buf, 0); /*"Il n'y a pas de voisinage d'une zone avec elle-meme,"*/
		informer(buf);
		cherchechaine(__FILE__, 12, buf, 0); /*"Les voisinages se font entre zones compatibles,"*/
		informer(buf);
		cherchechaine(__FILE__, 13, buf, 0); /*"La symetrie des voisinages est respectee."*/
		informer(buf);
	}
}

