#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

typedef enum {
	AUTRE, ANCIENNE, NOUVELLE, FUTURE
} STATUS;

typedef struct {
	_UNITE *unite;
	STATUS status;
} _UNITEPLUS;

typedef/**/ LISTE(_UNITEPLUS, NUNITES) _LISTEUNITEPLUS;
typedef/**/ LISTE(_UNITE *,NUNITES) _CHAINEUNITES;

/********************************************************************/

BOOL contactconvoi(_ZONE *zone1, _ZONE *zone2)
/* Permet de detecter qu'une flotte voisine de ESPCS peut convoyer une armee en ESP */
{
	_ZONE *p;

	if (zone1->specificite[0] == EOS)
		for (p = ZONE.t; p < ZONE.t + ZONE.n; p++) {
			if (p->region != zone1->region)
				continue;
			if (p == zone1)
				continue;
			if (flottevoisin(p, zone2))
				return TRUE;
		}

	if (zone2->specificite[0] == EOS)
		for (p = ZONE.t; p < ZONE.t + ZONE.n; p++) {
			if (p->region != zone2->region)
				continue;
			if (p == zone2)
				continue;
			if (flottevoisin(zone1, p))
				return TRUE;
		}

	return FALSE;
}

/********************************************************************/
/*             LES FONCTIONS                                        */
/********************************************************************/

BOOL convoinecessaire(_MOUVEMENT *mouvement)
/* Vrai si une armee sur une cote se rendant dans une autre ne peut le faire a pied */
{
	return mouvement->typemouvement == ATTAQUE
			&& mouvement->unite->zone->typezone == COTE
			&& mouvement->zonedest->typezone == COTE
			&& mouvement->unite->typeunite == ARMEE && !armeevoisin(
			mouvement->unite->zone, mouvement->zonedest);
}

BOOL convoipossible(_UNITE *unite, _ZONE *zone1, _ZONE *zone2)
/* Le convoi est possible si les flottes sont en place
 Si unite /= NULL on examine sans cette unite */
{
	_UNITE *p, **s;
	_ZONE *zone;
	_CHAINEUNITES LACHAINE, LACHAINE2;

	LACHAINE.n = 0;
	LACHAINE2.n = 0;
	p = UNITE.t;
	zone = zone1;

	for (;;) {

		while (p < UNITE.t + UNITE.n) {

			if (p->typeunite != FLOTTE) {
				p++;
				continue;
			}
			if (p->zone->typezone != MER) {
				p++;
				continue;
			}
			/* On ignore l'unite en question */
			if (unite != NULL && p == unite) {
				p++;
				continue;
			}
			for (s = LACHAINE2.t; s < LACHAINE2.t + LACHAINE2.n; s++)
				if (*s == p)
					break;
			if (s < LACHAINE2.t + LACHAINE2.n) { /* dans les exclus */
				p++;
				continue;
			}
			if (!(flottevoisin(zone, p->zone) || contactconvoi(zone, p->zone))) {
				p++;
				continue;
			}
			for (s = LACHAINE.t; s < LACHAINE.t + LACHAINE.n; s++)
				if (*s == p)
					break;
			if (s < LACHAINE.t + LACHAINE.n) { /* deja dans la chaine de convoi */
				p++;
				continue;
			}
			if (!flottevoisin(p->zone, zone2) && !contactconvoi(p->zone, zone2)) {

				LACHAINE.t[LACHAINE.n++] = p;
				assert(LACHAINE.n != NUNITES);
				zone = p->zone;
				p = UNITE.t;
				continue;
			}
			/* On arrive ici c'est que le convoi est possible */
			return TRUE;
		}

		if (LACHAINE.n != 0) {

			/* Pour le dernier, en impasse : */
			/* Mis dans les exclus */
			LACHAINE2.t[LACHAINE2.n++] = LACHAINE.t[LACHAINE.n - 1];
			assert(LACHAINE2.n != NUNITES);

			/* Retiré de la chaîne */
			LACHAINE.n--;
			assert(LACHAINE.n >= 0);

			if (LACHAINE.n == 0)
				zone = zone1;
			else
				zone = (LACHAINE.t[LACHAINE.n - 1])->zone;

			p = UNITE.t;
			continue;
		}

		return FALSE;
	}
}

BOOL convoiexiste(_ZONE *zone1, _ZONE *zone2)
/* Le convoi existe si des flotte bien placees ont recu l'ordre adequat */
{
	_UNITE *p, **s;
	_MOUVEMENT *q;
	_ZONE *zone;
	_CHAINEUNITES LACHAINE, LACHAINE2;
	BOOL ordredonne;

	LACHAINE.n = 0;
	LACHAINE2.n = 0;
	p = UNITE.t;
	zone = zone1;

	for (;;) {

		while (p < UNITE.t + UNITE.n) {
			for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
				if (q->unite == p)
					break;
			ordredonne = q->typemouvement == CONVOI && q->unitepass->zone
					== zone1 && q->zonedest == zone2;
			assert(q != MOUVEMENT.t + MOUVEMENT.n);
			if (!ordredonne) {
				p++;
				continue;
			}
			for (s = LACHAINE2.t; s < LACHAINE2.t + LACHAINE2.n; s++)
				if (*s == p)
					break;
			if (s < LACHAINE2.t + LACHAINE2.n) { /* dans les exclus */
				p++;
				continue;
			}
			if (!(flottevoisin(zone, p->zone) || contactconvoi(zone, p->zone))) {
				p++;
				continue;
			}
			for (s = LACHAINE.t; s < LACHAINE.t + LACHAINE.n; s++)
				if (*s == p)
					break;
			if (s < LACHAINE.t + LACHAINE.n) { /* deja dans la chaine de convoi */
				p++;
				continue;
			}
			if (!flottevoisin(p->zone, zone2) && !contactconvoi(p->zone, zone2)) {
				LACHAINE.t[LACHAINE.n++] = p;
				assert(LACHAINE.n != NUNITES);
				zone = p->zone;
				p = UNITE.t;
				continue;
			}
			/* On arrive ici c'est que le convoi existe */
			return TRUE;
		}

		if (LACHAINE.n != 0) {

			/* Pour le dernier, en impasse : */
			/* Mis dans les exclus */
			LACHAINE2.t[LACHAINE2.n++] = LACHAINE.t[LACHAINE.n - 1];
			assert(LACHAINE2.n != NUNITES);

			/* Retiré de la chaîne */
			LACHAINE.n--;
			assert(LACHAINE.n >= 0);

			if (LACHAINE.n == 0)
				zone = zone1;
			else
				zone = (LACHAINE.t[LACHAINE.n - 1])->zone;

			p = UNITE.t;
			continue;
		}

		return FALSE;

	}
}

BOOL convoivalide(_ZONE *zone1, _ZONE *zone2)
/* Le convoi existe si des flotte bien placees ont recu l'ordre adequat,
 de plus on trouve un chemin avec celles non delogees */
{
	_UNITE *p, **s;
	_MOUVEMENT *q;
	_ZONE *zone;
	_CHAINEUNITES LACHAINE, LACHAINE2;
	BOOL ordredonne;

	LACHAINE.n = 0;
	LACHAINE2.n = 0;
	p = UNITE.t;
	zone = zone1;

	for (;;) {

		while (p < UNITE.t + UNITE.n) {
			for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
				if (q->unite == p)
					break;
			assert(q != MOUVEMENT.t + MOUVEMENT.n);
			ordredonne = q->typemouvement == CONVOI && q->unitepass->zone
					== zone1 && q->zonedest == zone2;
			if (!ordredonne) {
				p++;
				continue;
			}

			/* Test si non delogee */
			if (unitedelogee(p)) {
				p++;
				continue;
			}
			if (!(flottevoisin(zone, p->zone) || contactconvoi(zone, p->zone))) {
				p++;
				continue;
			}
			for (s = LACHAINE.t; s < LACHAINE.t + LACHAINE.n; s++)
				if (*s == p)
					break;
			if (s < LACHAINE.t + LACHAINE.n) { /* deja dans la chaine de convoi */
				p++;
				continue;
			}
			for (s = LACHAINE2.t; s < LACHAINE2.t + LACHAINE2.n; s++)
				if (*s == p)
					break;
			if (s < LACHAINE2.t + LACHAINE2.n) { /* dans les exclus */
				p++;
				continue;
			}
			if (!flottevoisin(p->zone, zone2) && !contactconvoi(p->zone, zone2)) {
				LACHAINE.t[LACHAINE.n++] = p;
				assert(LACHAINE.n != NUNITES);
				zone = p->zone;
				p = UNITE.t;
				continue;
			}
			/* On arrive ici c'est que le convoi est valide */
			return TRUE;
		}

		if (LACHAINE.n != 0) {

			/* Pour le dernier, en impasse : */
			/* Mis dans les exclus */
			LACHAINE2.t[LACHAINE2.n++] = LACHAINE.t[LACHAINE.n - 1];
			assert(LACHAINE2.n != NUNITES);

			/* Retiré de la chaîne */
			LACHAINE.n--;
			assert(LACHAINE.n >= 0);

			if (LACHAINE.n == 0)
				zone = zone1;
			else
				zone = (LACHAINE.t[LACHAINE.n - 1])->zone;

			p = UNITE.t;
			continue;

		}

		return FALSE;
	}
}

BOOL empecheconvoi(_UNITE *unite, _ZONE *zone1, _ZONE *zone2)
/* Vrai si la flotte est indispensable au convoi */
{
	return !convoipossible(unite, zone1, zone2);
}

_UNITE *unitedupaysempechantconvoi(_PAYS *pays, _ZONE *zone1, _ZONE *zone2)
/* Vrai si le pays a saborde le convoi, I.e. une unite indispensable au convoi n'en a pas recu l'ordre */
{
	_UNITE *p;
	_MOUVEMENT *q;

	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++) {

		if (p->typeunite != FLOTTE)
			continue;

		if (p->zone->typezone != MER)
			continue;

		if (p->pays != pays)
			continue;

		/* Retrouve son ordre */
		for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
			if (q->unite == p)
				break;
		assert(q != MOUVEMENT.t + MOUVEMENT.n);
		if (q->typemouvement == CONVOI && q->unitepass->zone == zone1
				&& q->zonedest == zone2)
			continue;

		/* On a une flotte en mer du pays qui n'a pas donne l'ordre */
		/* Seul appel a convoi possible avec  unite /= NULL */
		if (empecheconvoi(p, zone1, zone2))
			return p;

	}

	/* Le pays est irreprochable */
	return NULL;
}

#if 0
BOOL peutconvoyer(_UNITE *flotte, _UNITE *armee)
/* Vrai si la flotte peut convoyer l'armée (chaine de flotte de la flotte à l'armée) */
{
	_UNITE *p, **s;
	_ZONE *zone;
	_CHAINEUNITES LACHAINE, LACHAINE2;

	LACHAINE.n = 0;
	LACHAINE2.n = 0;
	p = UNITE.t;
	zone = flotte->zone;

	/* Le bazar ci dessous ne detecte pas si acce direct flotte a armee */
	if(flottevoisin(flotte->zone,armee->zone) || contactconvoi(flotte->zone,armee->zone))
	return TRUE;

	for(;;) {
		while(p < UNITE.t + UNITE.n) {

			if(p->typeunite != FLOTTE) {
				p++;
				continue;
			}
			if(p->zone->typezone != MER) {
				p++;
				continue;
			}
			for(s = LACHAINE2.t; s < LACHAINE2.t + LACHAINE2.n; s++)
			if(*s == p)
			break;
			if(s < LACHAINE2.t + LACHAINE2.n) { /* dans les exclus */
				p++;
				continue;
			}

			if(!(flottevoisin(zone,p->zone) || contactconvoi(zone,p->zone))) {
				p++;
				continue;
			}

			for(s = LACHAINE.t; s < LACHAINE.t + LACHAINE.n; s++)
			if(*s == p)
			break;
			if(s < LACHAINE.t + LACHAINE.n) { /* deja dans la chaine de convoi */
				p++;
				continue;
			}

			if(!flottevoisin(p->zone,armee->zone) && !contactconvoi(p->zone,armee->zone)) {

				LACHAINE.t[LACHAINE.n++] = p;
				assert(LACHAINE.n != NUNITES);
				zone = p->zone;
				p = UNITE.t;
				continue;
			}
			/* On arrive ici c'est que le convoi est possible */
			return TRUE;
		}

		if(LACHAINE.n != 0) {

			/* Pour le dernier, en impasse : */
			/* Mis dans les exclus */
			LACHAINE2.t[LACHAINE2.n++] = LACHAINE.t[LACHAINE.n-1];
			assert(LACHAINE2.n != NUNITES);

			/* Retiré de la chaîne */
			LACHAINE.n--;
			assert(LACHAINE.n >= 0);

			if(LACHAINE.n == 0)
			zone = flotte->zone;
			else
			zone = (LACHAINE.t[LACHAINE.n-1])->zone;

			p = UNITE.t;
			continue;
		}

		return FALSE;
	}
}
#endif

BOOL peutconvoyer(_UNITE *flotte, _UNITE *armee, _ZONE *zonedest)
/* Vrai si la flotte peut convoyer l'armée (chaine de flotte de la flotte à l'armée)
 si zonedest /= NULL on verifie meme que la flotte est utile au convoi vers la 'zonedest' */
{
	_UNITE *p;
	_LISTEUNITEPLUS LACHAINE;
	_UNITEPLUS *q, *r;
	BOOL dunouveau;
	BOOL flottetrouvee = FALSE;

	/* Liste des flottes en mer */
	LACHAINE.n = 0;
	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++) {

		/* Flotte */
		if (p->typeunite != FLOTTE)
			continue;

		/* En mer */
		if (p->zone->typezone != MER)
			continue;

		LACHAINE.t[LACHAINE.n].unite = p;
		LACHAINE.t[LACHAINE.n].status = (flottevoisin(armee->zone, p->zone)
				|| contactconvoi(armee->zone, p->zone) ? NOUVELLE : AUTRE);
		LACHAINE.n++;

	}

	if (LACHAINE.n == 0)
		return FALSE;

	for (;;) {

		/* Est - elle voisine d'une des cibles (flotte qui convoie ou zone destination) ? */
		for (q = LACHAINE.t; q < LACHAINE.t + LACHAINE.n; q++) {

			if (q->status != NOUVELLE)
				continue;

			if (q->unite == flotte) {
				flottetrouvee = TRUE;
				if (zonedest == NULL)
					return TRUE;
			}

			if (flottetrouvee && zonedest != NULL && (flottevoisin(
					q->unite->zone, zonedest) || contactconvoi(q->unite->zone,
					zonedest)))
				return TRUE;
		}

		dunouveau = FALSE;
		for (q = LACHAINE.t; q < LACHAINE.t + LACHAINE.n; q++) {

			/* Est elle dans les anciennes ? */
			if (q->status == ANCIENNE)
				continue;

			/* Est elle dans les nouvelles ? */
			if (q->status == NOUVELLE)
				continue;

			/* Est-elle voisine d'une nouvelle ? */
			for (r = LACHAINE.t; r < LACHAINE.t + LACHAINE.n; r++) {

				if (r->status != NOUVELLE)
					continue;

				/* voisinage */
				if (flottevoisin(r->unite->zone, q->unite->zone))
					break;

			}

			if (r == LACHAINE.t + LACHAINE.n)
				continue;

			q->status = FUTURE; /* Voisine d'une nouvelle :
			 * mis dans les futures */
			dunouveau = TRUE;

		}

		if (!dunouveau)
			return FALSE;

		/* Les nouvelles passent dans les anciennes */
		for (q = LACHAINE.t; q < LACHAINE.t + LACHAINE.n; q++)
			if (q->status == NOUVELLE)
				q->status = ANCIENNE;

		/* les futures passent dans les nouvelles */
		for (q = LACHAINE.t; q < LACHAINE.t + LACHAINE.n; q++)
			if (q->status == FUTURE)
				q->status = NOUVELLE;

	} /* boucle infinie */

}
