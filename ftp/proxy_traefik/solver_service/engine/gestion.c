#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

extern int noligne; /* Ligne dans fichier ou synonyme à déconseilller */

/* Pour accelerer la recherche des voisinages, on stoque dans une table */
BOOL TABLEVOISINAGEFLOTTE[NZONES][NZONES];
BOOL TABLEVOISINAGEARMEE[NZONES][NZONES];

/*************************************************************************/
/*        DEUX FONCTIONS UTILES                                          */
/*************************************************************************/

BOOL compatibles(TYPEUNITE typeunite, _ZONE *zone)
/* Verifie qu'un armee ne va pas en mer et qu'une flotte ne va pas en terre */
{
	_ZONE *q;

	if (typeunite == FLOTTE && !strcmp(zone->specificite, ""))
		for (q = ZONE.t; q < ZONE.t + ZONE.n; q++)
			if (q->region == zone->region && strcmp(q->specificite, ""))
				return FALSE;
	return (typeunite == FLOTTE && (zone->typezone == MER || zone->typezone
			== COTE)) || (typeunite == ARMEE && (zone->typezone == TERRE
			|| (zone->typezone == COTE && zone->specificite[0] == EOS)));
}

void lesajustements(_PAYS *pays, int *possessions, int *unites, int *possibles) {
	_POSSESSION *s;
	_CENTREDEPART *v;
	_UNITE *t;

	(*possessions) = 0;
	for (s = POSSESSION.t; s < POSSESSION.t + POSSESSION.n; s++)
		if (s->pays == pays)
			(*possessions)++;

	(*unites) = 0;
	for (t = UNITE.t; t < UNITE.t + UNITE.n; t++)
		if (t->pays == pays)
			(*unites)++;


	if(!OPTIONE) {
		/* standard : can only build on start centers */
		(*possibles) = 0;
		for (v = CENTREDEPART.t; v < CENTREDEPART.t + CENTREDEPART.n; v++) {
			if (v->pays != pays)
				continue; /* pas centre de depart du bon pays */

			for (t = UNITE.t; t < UNITE.t + UNITE.n; t++)
				if (t->zone->region == v->centre->region)
					break;
			if (t != UNITE.t + UNITE.n)
				continue; /* centre occupe */

			for (s = POSSESSION.t; s < POSSESSION.t + POSSESSION.n; s++)
				if (s->centre == v->centre)
					break;
			if (s == POSSESSION.t + POSSESSION.n)
				continue; /* centre possede par personne */
			else if (s->pays != pays)
				continue; /* centre possede par un autre */

			(*possibles)++;
		}
	} else {
		/* can build on all owned centers */
		(*possibles) = 0;
		for (s = POSSESSION.t; s < POSSESSION.t + POSSESSION.n; s++) {
			if (s->pays != pays)
				continue; /* pas possession  du bon pays */

			for (t = UNITE.t; t < UNITE.t + UNITE.n; t++)
				if (t->zone->region == s->centre->region)
					break;
			if (t != UNITE.t + UNITE.n)
				continue; /* centre occupe */

			(*possibles)++;
		}
	}
}

/*************************************************************************/
/*        FONCTIONS CONVERSION PAYS <-> NUMERO                           */
/*************************************************************************/
_PAYS *paysdinitiale(int c) {
	_PAYS *p;

	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
		if (p->initiale == c)
			return p;

	assert(FALSE); /* On ne doit pas passer par la */
	return NULL; /* Trompe le compilateur */
}

/*************************************************************************/
/*        CES FONCTIONS CHERCHENT SI UN OBJET EXISTE                     */
/*************************************************************************/

BOOL contactsoutienarmee(_ZONE *zone1, _ZONE *zone2)
/* Renvoie vrai si une armee en zone1 peut soutenir off/def sur zone2 */
{
	_ZONE *p;

	if (zone2->specificite[0] != EOS)
		for (p = ZONE.t; p < ZONE.t + ZONE.n; p++) {
			if (p->region != zone2->region)
				continue;
			if (p == zone2)
				continue;
			if (armeevoisin(p, zone1))
				return TRUE;
		}

	return FALSE;
}

BOOL contactsoutienflotte(_ZONE *zone1, _ZONE *zone2)
/* Renvoie vrai si une flotte en zone1 peut soutenir off/def sur zone2 */
{
	_ZONE *p;

	for (p = ZONE.t; p < ZONE.t + ZONE.n; p++) {
		if (p->region != zone2->region)
			continue;
		if (p == zone2)
			continue;
		if (flottevoisin(p, zone1))
			return TRUE;
	}

	return FALSE;
}

int eloignement(TYPEUNITE typeunite, _ZONE *zone, _PAYS *pays)
/* Renvoie l'eloignement de la zone au pays */
{
	_ELOIGNEMENT *p;

	for (p = ELOIGNEMENT.t; p < ELOIGNEMENT.t + ELOIGNEMENT.n; p++)
		if (p->typeunite == typeunite && p->zone == zone && p->pays == pays)
			return p->valeur;

	assert(FALSE); /* On ne doit pas passer par la */
	return 0; /* Trompe le compilateur */
}

BOOL possede(_PAYS *pays, _CENTRE *centre)
/* Renvoie vrai si le pays possede le centre */
{
	_POSSESSION *p;

	for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++)
		if (p->pays == pays && p->centre == centre)
			return TRUE;

	return FALSE;
}

/* Cette fonction est utilisee par le ploteur */
BOOL centrepossede(_CENTRE *centre)
/* Renvoie vrai si un pays possede le centre */
{
	_POSSESSION *p;

	for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++)
		if (p->centre == centre)
			return TRUE;

	return FALSE;
}

BOOL interditretraite(_REGION *region)
/* Renvoie vrai si la region est interdite en retraite */
{
	_INTERDIT *p;

	for (p = INTERDIT.t; p < INTERDIT.t + INTERDIT.n; p++) {
		if (p->region == region)
			return TRUE;
	}
	return FALSE;
}

BOOL unitedelogee(_UNITE *unite)
/* Renvoie vrai si l'unite est delogee - aneantie ou pas */
{
	_DELOGEE *p;

	for (p = DELOGEE.t; p < DELOGEE.t + DELOGEE.n; p++) {
		if (p->unite == unite)
			return TRUE;
	}
	return FALSE;
}

BOOL uniteaneantie(_UNITE *unite)
/* Renvoie vrai si l'unite est aneantie - sans retraite possible */
{
	_ANEANTIE *p;

	for (p = ANEANTIE.t; p < ANEANTIE.t + ANEANTIE.n; p++) {

		if (p->delogee->unite == unite)
			return TRUE;
	}
	return FALSE;
}

_UNITE *chercheoccupant(_REGION *region) {
	_UNITE *p;

	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++)
		if (p->zone->region == region)
			return p;

	return NULL;
}

_UNITE *chercheoccupantnondeloge(_REGION *region) {
	_UNITE *p;
	_DELOGEE *q;

	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++)
		if (p->zone->region == region) {
			for (q = DELOGEE.t; q < DELOGEE.t + DELOGEE.n; q++)
				if(q->unite == p)
					break;
			if(q == DELOGEE.t + DELOGEE.n)
				return p;
		}

	return NULL;
}

/*************************************************************************/
/*        CES FONCTIONS CHERCHENT DES OBJETS D'APRES LEUR NOM            */
/*************************************************************************/

_PAYS *cherchepays(char *s) {
	_PAYS *p;

	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
		if (!strcmp(p->nom, s))
			return p;

	return NULL;
}

_PAYS *chercheadjectifpays(char *s) {
	_PAYS *p;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
		if (!strcmp(p->adjectif, s))
			return p;

	/* We do not consider OPTIONL here */
	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
		if (!strcmp(p->nom, s)) {
			(void) sprintf(bufn1, "%d", noligne);
			cherchechaine(__FILE__, 3, buf, 3, p->adjectif, p->nom, bufn1); /*"Utiliser '%1' plutot que '%2' pour un pays passif en ligne %3"*/
			informer(buf);
			return p;
		}

	return NULL;
}

_CENTRE *cherchecentre(char *s) {
	_CENTRE *p;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	for (p = CENTRE.t; p < CENTRE.t + CENTRE.n; p++)
		if (!strcmp(p->region->nom, s))
			return p;

	/* We do not consider OPTIONL here */
	for (p = CENTRE.t; p < CENTRE.t + CENTRE.n; p++)
		if (!strcmp(p->region->nom2, s)) {
			(void) sprintf(bufn1, "%d", noligne);
			cherchechaine(__FILE__, 4, buf, 3, p->region->nom, p->region->nom2,
					bufn1); /*"Utiliser '%1' plutot que '%2' pour un centre en ligne %3"*/
			informer(buf);
			return p;
		}

	return NULL;
}

_CENTREDEPART *cherchecentredepart(char *s) {
	_CENTREDEPART *p;
	char c = *s;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	for (p = CENTREDEPART.t; p < CENTREDEPART.t + CENTREDEPART.n; p++) {
		if (*(p->centre->region->nom) == c) { /* Optimisation tres efficace */
			if (!strcmp(p->centre->region->nom, s))
				return p;
		}
	}

	/* We do not consider OPTIONL here */
	for (p = CENTREDEPART.t; p < CENTREDEPART.t + CENTREDEPART.n; p++) {
		if ((*(p->centre->region->nom) == c) && /* Optimisation tres efficace */
		!strcmp(p->centre->region->nom2, s)) {
			(void) sprintf(bufn1, "%d", noligne);
			cherchechaine(__FILE__, 5, buf, 3, p->centre->region->nom,
					p->centre->region->nom2, bufn1); /*"Utiliser '%1' plutot que '%2' pour un centredepart en ligne %3"*/
			informer(buf);
			return p;
		}
	}

	return NULL;

}

_UNITE *chercheuniteavecpays(char *s) {
	_UNITE *p;
	char nomunite[3 * TAILLEMOT], buf[TAILLEMESSAGE];
	char c = *s;
	char bufn1[TAILLEENTIER];

	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++) {
		if (*(p->zone->region->nom) == c) { /* Optimisation tres efficace */
			(void) strcpy(nomunite, p->zone->region->nom);
			(void) strcat(nomunite, p->zone->specificite);
			(void) strcat(nomunite, p->pays->nom);
			(void) strcat(nomunite, (p->typeunite == ARMEE ? "A" : "F"));
			if (!strcmp(nomunite, s))
				return p;
		}
	}

	/* We do not consider OPTIONL here */
	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++) {
		if (*(p->zone->region->nom) == c) { /* Optimisation tres efficace */
			(void) strcpy(nomunite, p->zone->region->nom2);
			(void) strcat(nomunite, p->zone->specificite);
			(void) strcat(nomunite, p->pays->nom);
			(void) strcat(nomunite, (p->typeunite == ARMEE ? "A" : "F"));
			if (!strcmp(nomunite, s)) {
				(void) sprintf(bufn1, "%d", noligne);
				cherchechaine(__FILE__, 6, buf, 3, p->zone->region->nom,
						p->zone->region->nom2, bufn1); /*"Utiliser '%1' plutot que '%2' pour une unite en ligne %3"*/
				informer(buf);
				return p;
			}
		}
	}

	return NULL;
}

_DELOGEE *cherchedelogee(char *s) {
	_DELOGEE *p;
	char nomunite[3 * TAILLEMOT], buf[TAILLEMESSAGE];
	char c = *s;
	char bufn1[TAILLEENTIER];

	for (p = DELOGEE.t; p < DELOGEE.t + DELOGEE.n; p++) {
		if (*(p->unite->pays->nom) == c) { /* Optimisation tres efficace */
			(void) strcpy(nomunite, p->unite->pays->nom);
			(void) strcat(nomunite, p->unite->zone->region->nom);
			(void) strcat(nomunite, p->unite->zone->specificite);
			(void) strcat(nomunite, (p->unite->typeunite == ARMEE ? "A" : "F"));
			if (!strcmp(nomunite, s))
				return p;
		}
	}

	/* We do not consider OPTIONL here */
	for (p = DELOGEE.t; p < DELOGEE.t + DELOGEE.n; p++) {
		if (*(p->unite->pays->nom) == c) { /* Optimisation tres efficace */
			(void) strcpy(nomunite, p->unite->pays->nom);
			(void) strcat(nomunite, p->unite->zone->region->nom2);
			(void) strcat(nomunite, p->unite->zone->specificite);
			(void) strcat(nomunite, (p->unite->typeunite == ARMEE ? "A" : "F"));
			if (!strcmp(nomunite, s)) {
				(void) sprintf(bufn1, "%d", noligne);
				cherchechaine(__FILE__, 7, buf, 3, p->unite->zone->region->nom,
						p->unite->zone->region->nom2, bufn1); /*"Utiliser '%1' plutot que '%2' pour une delogee en ligne %3"*/
				informer(buf);
				return p;
			}
		}
	}

	return NULL;
}

_REGION *chercheregion(char *s) {
	_REGION *p;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	for (p = REGION.t; p < REGION.t + REGION.n; p++)
		if (!strcmp(p->nom, s))
			return p;

	/* We do not consider OPTIONL here */
	for (p = REGION.t; p < REGION.t + REGION.n; p++)
		if (!strcmp(p->nom2, s)) {
			(void) sprintf(bufn1, "%d", noligne);
			cherchechaine(__FILE__, 8, buf, 3, p->nom, p->nom2, bufn1); /*"Utiliser '%1' plutot que '%2' pour une region en ligne %3"*/
			informer(buf);
			return p;
		}

	return NULL;
}

BOOL cotesexistent(_ZONE *zone) {
	_ZONE *p;

	for (p = ZONE.t; p < ZONE.t + ZONE.n; p++) {
		if (p->region != zone->region)
			continue;
		if (p == zone)
			continue;
		if (strcmp(p->specificite, ""))
			return TRUE;
	}

	return FALSE;
}

_UNITE *chercheunite(char *s) {
	_UNITE *p;
	char nomunite[3 * TAILLEMOT], buf[TAILLEMESSAGE];
	char c = *s;
	char bufn1[TAILLEENTIER];

	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++)
		if (*(p->zone->region->nom) == c) { /* Optimisation tres efficace */
			(void) strcpy(nomunite, p->zone->region->nom);
			(void) strcat(nomunite, p->zone->specificite);
			(void) strcat(nomunite, (p->typeunite == ARMEE ? "A" : "F"));
			if (!strcmp(nomunite, s))
				return p;
		}

	/* We do not consider OPTIONL here */
	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++)
		if (*(p->zone->region->nom2) == c) {
			(void) strcpy(nomunite, p->zone->region->nom2);
			(void) strcat(nomunite, p->zone->specificite);
			(void) strcat(nomunite, (p->typeunite == ARMEE ? "A" : "F"));
			if (!strcmp(nomunite, s)) {
				(void) sprintf(bufn1, "%d", noligne);
				cherchechaine(__FILE__, 9, buf, 3, p->zone->region->nom,
						p->zone->region->nom2, bufn1); /*"Utiliser '%1' plutot que '%2' pour une unite en ligne %3"*/
				informer(buf);
				return p;
			}
		}

	return NULL;
}

_ZONE *cherchezone(char *s) {
	_ZONE *p;
	char nomzone[2 * TAILLEMOT], buf[TAILLEMESSAGE];
	char c = *s;
	char bufn1[TAILLEENTIER];

	for (p = ZONE.t; p < ZONE.t + ZONE.n; p++)
		if (*(p->region->nom) == c) { /* Optimisation tres efficace */
			(void) strcpy(nomzone, p->region->nom);
			(void) strcat(nomzone, p->specificite);
			if (!strcmp(nomzone, s))
				return p;
		}

	/* We do not consider OPTIONL here */
	for (p = ZONE.t; p < ZONE.t + ZONE.n; p++)
		if (*(p->region->nom2) == c) { /* Optimisation tres efficace */
			(void) strcpy(nomzone, p->region->nom2);
			(void) strcat(nomzone, p->specificite);
			if (!strcmp(nomzone, s)) {
				(void) sprintf(bufn1, "%d",  noligne);
				cherchechaine(__FILE__, 10, buf, 3, p->region->nom,
						p->region->nom2, bufn1); /*"Utiliser '%1' plutot que '%2' pour une zone en ligne %3"*/
				informer(buf);
				return p;
			}
		}

	return NULL;
}

/*************************************************************************/
/*        AUTRES FONCTIONS                                              */
/*************************************************************************/

BOOL armeevoisin(_ZONE *zone1, _ZONE *zone2) {
	return TABLEVOISINAGEARMEE[zone1->rang][zone2->rang];
}

BOOL flottevoisin(_ZONE *zone1, _ZONE *zone2) {
	return TABLEVOISINAGEFLOTTE[zone1->rang][zone2->rang];
}

void initialisetablevoisinages(void)
/* Initialise la table des voisinages a tout faux */
{
	int i, j;
	_ZONE *p, *q;

	for (p = ZONE.t, i = 0; p < ZONE.t + ZONE.n; p++, i++)
		for (q = ZONE.t, j = 0; q < ZONE.t + ZONE.n; q++, j++) {
			TABLEVOISINAGEARMEE[i][j] = FALSE;
			TABLEVOISINAGEFLOTTE[i][j] = FALSE;
		}

}
