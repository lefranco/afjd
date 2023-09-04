#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

#define INFINITE 2147483647

typedef/**/ LISTE(_ZONE *, NZONES) _CHAINEZONES;


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

