#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

/* #define DEBUG */

typedef struct {
	_PAYS *pays;
	int nbcentres, partage, place, score;
} _PAYSBILAN;

typedef/**/ LISTE(_UNITE *,NUNITES) _SUPPRESSIONS;

typedef int INDEXUNITE[NUNITES];
typedef int INDEXDELOGEE[NDELOGEES];

static int valpays(_PAYS *);
static void decritmouvements(FILE *, _PAYS *, BOOL);
static void decritretraites(FILE *, _PAYS *, BOOL);
static void decritajustements(FILE *, _PAYS *, BOOL);
static void classeunites(TUNITE, INDEXUNITE);
static void classedelogees(TDELOGEE, INDEXDELOGEE);
static void infospreajustements(FILE *);

#ifdef DEBUG
void decritcarte(void)
{
	_PAYS *p;
	_REGION *q;
	_CENTRE *r;
	_CENTREDEPART *s;
	_ZONE *t;
	SPECIFICITE specif;

	(void) printf("; LA CARTE : \n\n");

	(void) printf("PAYS\n");
	for(p = PAYS.t; p < PAYS.t + PAYS.n; p++)
	(void) printf("%s\n",p->nom);

	(void) printf("\nREGIONS\n");
	for(q = REGION.t; q < REGION.t + REGION.n; q++)
	(void) printf("%s\n",q->nom);

	(void) printf("\nCENTRES\n");
	for(r = CENTRE.t; r < CENTRE.t + CENTRE.n; r++)
	(void) printf("%s\n",r->region->nom);

	(void) printf("\nCENTREDEPARTS\n");
	for(s = CENTREDEPART.t; s < CENTREDEPART.t + CENTREDEPART.n; s++)
	(void) printf("%s %s\n",s->pays->nom,s->centre->region->nom);

	(void) printf("\nZONES\n");
	for(t = ZONE.t; t < ZONE.t + ZONE.n; t++) {
		(void) strcpy(specif, t->specificite);
		Strlwr(specif);
		(void) printf("%s %s%s\n",
				(t->typezone == MER ? "mer" : (t->typezone == TERRE ? "terre" : "cote")),
				t->region->nom, specif);
	}
	(void) printf("\n");
}
#endif

void decritsituation(char *nomfic)
/* Dump la situation pour le prochain appel a "diplo" */
{
	FILE *fd;
	_UNITE *p;
	_POSSESSION *q;
	_INTERDIT *r;
	_DELOGEE *s;
	_DISPARITION *t;
	SPECIFICITE specif;
	char buf[TAILLEMESSAGE];

	if (!strcmp(nomfic, ""))
		return;

	if ((fd = fopen(nomfic, "w")) == NULL) {
		cherchechaine(__FILE__, 1, buf, 0); /*"Impossible de dumper la situation finale"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	(void) fprintf(fd, "SAISON %s %d\n", NOMSAISON[SAISON % NSAISONS], ANNEEZERO
			+ (SAISON / NSAISONS));
	(void) fprintf(fd, "SAISONMODIF %s %d\n\n", NOMSAISON[SAISONMODIF
			% NSAISONS], ANNEEZERO + (SAISONMODIF / NSAISONS));

	(void) fprintf(fd, ";LES POSSESSIONS\n");
	for (q = POSSESSION.t; q < POSSESSION.t + POSSESSION.n; q++)
		(void) fprintf(fd, "POSSESSION %s %s\n", q->pays->nom,
				q->centre->region->nom);
	(void) fprintf(fd, "\n");

	(void) fprintf(fd, ";LES UNITES\n");
	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++) {
		(void) strcpy(specif, p->zone->specificite);
		Strlwr(specif);
		if (uniteaneantie(p))
			(void) fprintf(fd, ";");
		(void) fprintf(fd, "UNITE %s %s %s%s\n", (p->typeunite == ARMEE ? "A"
				: "F"), p->pays->nom, p->zone->region->nom, specif);
	}
	(void) fprintf(fd, "\n");

	switch ((IDSAISON) (SAISON % NSAISONS)) {

	case ETE:
	case HIVER:

		(void) fprintf(fd, "; LES INTERDITS EN RETRAITE\n");
		for (r = INTERDIT.t; r < INTERDIT.t + INTERDIT.n; r++)
			(void) fprintf(fd, "INTERDIT %s\n", r->region->nom);
		(void) fprintf(fd, "\n");

		(void) fprintf(fd, "; LES UNITES DELOGEES\n");
		for (s = DELOGEE.t; s < DELOGEE.t + DELOGEE.n; s++) {
			(void) strcpy(specif, s->unite->zone->specificite);
			Strlwr(specif);
			if (uniteaneantie(s->unite))
				(void) fprintf(fd, ";");
			(void) fprintf(fd, "DELOGEE %s %s %s%s ", (s->unite->typeunite
					== ARMEE ? "A" : "F"), s->unite->pays->nom,
					s->unite->zone->region->nom, specif);
			(void) strcpy(specif, s->uniteorig->zone->specificite);
			Strlwr(specif);
			(void) fprintf(fd, "BOURREAU %s %s %s%s ", (s->uniteorig->typeunite
					== ARMEE ? "A" : "F"), s->uniteorig->pays->nom,
					s->uniteorig->zone->region->nom, specif);
			(void) strcpy(specif, s->zoneorig->specificite);
			Strlwr(specif);
			(void) fprintf(fd, "ORIGINE %s%s\n", s->zoneorig->region->nom,
					specif);
		}
		(void) fprintf(fd, "\n");

		break;

	default:

		/* Rien a faire */
		break;

	}

	(void) fprintf(fd, ";LES DISPARITIONS\n");
	for (t = DISPARITION.t; t < DISPARITION.t + DISPARITION.n; t++) {
		(void) fprintf(fd, "DISPARITION %s %d\n", t->pays->nom, t->annee);
	}
	(void) fprintf(fd, "\n");

}

/**********************************************************************/
/* Ces procedures produisent des fichiers lisibles                    */
/**********************************************************************/

static int valpays(_PAYS *pays)
/* Met une note a un pays, meilleure plus il a de centres, departage par
 les unites non placees sur un centre */
{
	int ncentres, nuniteshorscentre;
	_POSSESSION *q;
	_UNITE *r;
	_CENTRE *s;

	ncentres = 0;
	for (q = POSSESSION.t; q < POSSESSION.t + POSSESSION.n; q++) {
		if (q->pays == pays)
			ncentres++;
	}

	nuniteshorscentre = 0;
	for (r = UNITE.t; r < UNITE.t + UNITE.n; r++)
		if (r->pays == pays) {
			for (s = CENTRE.t; s < CENTRE.t + CENTRE.n; s++)
				if (s->region == r->zone->region)
					break;
			if (s == CENTRE.t + CENTRE.n)
				nuniteshorscentre++;
		}

	return NUNITES * ncentres + nuniteshorscentre;
}

/* Pour le ploteur */
void classementpays(void)
/* Affiche les pays classes dans l'ordre defini ci dessus */
{
	_PAYS *p, **q, *paysrec;
	int valrec, n;

	paysrec = NULL; /* Evite un avertissement du compilateur */

	PAYSCLASSES.n = 0;
	for (;;) {
		valrec = 0;
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++) {
			for (q = PAYSCLASSES.t; q < PAYSCLASSES.t + PAYSCLASSES.n; q++)
				if (*q == p)
					break;
			if (q == PAYSCLASSES.t + PAYSCLASSES.n) {
				n = valpays(p);
				if (n > valrec) {
					valrec = n;
					paysrec = p;
				}
			}
		}

		if (valrec == 0)
			break;
		PAYSCLASSES.t[PAYSCLASSES.n] = paysrec;
		PAYSCLASSES.n++;
		assert(PAYSCLASSES.n != NPAYSS);
	}
}

void calculajustements(_PAYS *pays, int *ncentres, int *nunites,
		int *najustementspossibles) {
	_POSSESSION *q;
	_UNITE *r;
	_CENTREDEPART *v;

	*nunites = 0;
	for (r = UNITE.t; r < UNITE.t + UNITE.n; r++)
		if (r->pays == pays)
			(*nunites)++;

	*ncentres = 0;
	for (q = POSSESSION.t; q < POSSESSION.t + POSSESSION.n; q++)
		if (q->pays == pays)
			(*ncentres)++;

	*najustementspossibles = 0;
	for (v = CENTREDEPART.t; v < CENTREDEPART.t + CENTREDEPART.n; v++) {
		if (v->pays != pays)
			continue; /* pas centre de depart du bon pays */
		for (r = UNITE.t; r < UNITE.t + UNITE.n; r++)
			if (r->zone->region == v->centre->region)
				break;
		if (r != UNITE.t + UNITE.n)
			continue; /* centre occupe */

		for (q = POSSESSION.t; q < POSSESSION.t + POSSESSION.n; q++)
			if (q->centre == v->centre && q->pays == pays)
				(*najustementspossibles)++;
	}
}

static void decritmouvements(FILE *fd, _PAYS *pays, BOOL affpays) {
	_MOUVEMENT *p, *prec;
	_ANEANTIE *q;
	_DELOGEE *s;
	SPECIFICITE specif;
	char buf[TAILLEMESSAGE];
	char nompays[TAILLEMOT], trigramme[TAILLEMOT];

	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		if (p->unite->pays == pays)
			break;
	if (p == MOUVEMENT.t + MOUVEMENT.n)
		return;

	if (affpays)
		(void) fprintf(fd, "%s\n", pays->nom);

	(void) strcpy(trigramme, "");

	for (;;) {

		prec = NULL;

		/* On cherche l'unite de plus faible trigramme supérieur à celui qu'on vien d'afficher */
		for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

			if (p->unite->pays != pays)
				continue;

			if (strcmp(p->unite->zonedepart->region->nom, trigramme) <= 0)
				continue;

			if (prec == NULL || strcmp(p->unite->zonedepart->region->nom,
					prec->unite->zonedepart->region->nom) < 0)
				prec = p;

		}

		/* Si on a pas trouve on arrete tout */
		if (prec == NULL) {
			(void) fprintf(fd, "\n");
			break;
		}

		p = prec;
		(void) strcpy(trigramme, p->unite->zonedepart->region->nom);

		(void) strcpy(specif, p->unite->zonedepart->specificite);
		Strlwr(specif);
		(void) fprintf(fd, "%s %s%s",
				(p->unite->typeunite == ARMEE ? "A" : "F"),
				p->unite->zonedepart->region->nom, specif);

		switch (p->typemouvement) {

		case STAND:
			(void) fprintf(fd, " %c", (p->valable ? 'H' : 'h'));
			break;

		case ATTAQUE:
			(void) strcpy(specif, p->zonedest->specificite);
			Strlwr(specif);

			(void) fprintf(fd, " - %s%s", p->zonedest->region->nom, specif);
			if (!p->valable) {
				cherchechaine(__FILE__, 16, buf, 0); /*";(f)"*/
				(void) fprintf(fd, "%s", buf);
			}
			break;

		case SOUTIENDEF:
			(void) strcpy(specif, p->unitepass->zonedepart->specificite);
			Strlwr(specif);

			(void) strcpy(nompays, p->unitepass->pays->adjectif);
			Strlwr(nompays);

			(void) fprintf(fd, " %c", (p->valable ? 'S' : 's'));

			if((p->unitepass->pays != p->unite->pays)) {
				(void) fprintf(fd, " %s", nompays);
			}

			(void) fprintf(fd, " %s %s%s",
					(p->unitepass->typeunite == ARMEE ? "A" : "F"),
					p->unitepass->zonedepart->region->nom, specif);

			if (p->coupe) {
				cherchechaine(__FILE__, 19, buf, 0); /*";(c)"*/
				(void) fprintf(fd, "%s", buf);
			}
			if (p->paradoxe) {
				cherchechaine(__FILE__, 22, buf, 0); /*";(p)"*/
				(void) fprintf(fd, "%s", buf);
			}
			if (p->dedaigne) {
				cherchechaine(__FILE__, 39, buf, 0); /*";(v)"*/
				(void) fprintf(fd, "%s", buf);
			}
			break;

		case SOUTIENOFF:
			(void) strcpy(specif, p->unitepass->zonedepart->specificite);
			Strlwr(specif);

			(void) strcpy(nompays, p->unitepass->pays->adjectif);
			Strlwr(nompays);

			(void) fprintf(fd, " %c", (p->valable ? 'S' : 's'));

			if(p->unitepass->pays != p->unite->pays) {
				(void) fprintf(fd, " %s", nompays);
			}

			(void) fprintf(fd, " %s %s%s",
					(p->unitepass->typeunite == ARMEE ? "A" : "F"),
					p->unitepass->zonedepart->region->nom, specif);

			(void) strcpy(specif, p->zonedest->specificite);
			Strlwr(specif);

			(void) fprintf(fd, " - %s%s", p->zonedest->region->nom, specif);
			if (p->coupe) {
				cherchechaine(__FILE__, 19, buf, 0); /*";(c)"*/
				(void) fprintf(fd, "%s", buf);
			}
			if (p->paradoxe) {
				cherchechaine(__FILE__, 22, buf, 0); /*";(p)"*/
				(void) fprintf(fd, "%s", buf);
			}
			if (p->dedaigne) {
				cherchechaine(__FILE__, 40, buf, 0); /*";(v)"*/
				(void) fprintf(fd, "%s", buf);
			}
			break;

		case CONVOI:
			(void) strcpy(specif, p->unitepass->zonedepart->specificite);
			Strlwr(specif);

			(void) strcpy(nompays, p->unitepass->pays->adjectif);
			Strlwr(nompays);

			(void) fprintf(fd, " %c", (p->valable ? 'C' : 'c'));

			if(p->unitepass->pays != p->unite->pays) {
				(void) fprintf(fd, " %s", nompays);
			}

			(void) fprintf(fd, " %s %s%s",
					(p->unitepass->typeunite == ARMEE ? "A" : "F"),
					p->unitepass->zonedepart->region->nom, specif);

			(void) strcpy(specif, p->zonedest->specificite);
			Strlwr(specif);

			(void) fprintf(fd, " - %s%s", p->zonedest->region->nom, specif);
			if (p->dedaigne) {
				cherchechaine(__FILE__, 41, buf, 0); /*";(v)"*/
				(void) fprintf(fd, "%s", buf);
			}
			break;
		}

		for (s = DELOGEE.t; s < DELOGEE.t + DELOGEE.n; s++)
			if (s->unite == p->unite) {
				cherchechaine(__FILE__, 17, buf, 0); /*";(d)"*/
				(void) fprintf(fd, "%s", buf);
				for (q = ANEANTIE.t; q < ANEANTIE.t + ANEANTIE.n; q++)
					if (q->delogee == s) {
						cherchechaine(__FILE__, 18, buf, 0); /*";(a)"*/
						(void) fprintf(fd, "%s", buf);
						break;
					}
				break;
			}

		if (p->noligne == 0) {
			cherchechaine(__FILE__, 20, buf, 0); /*";PAR DEFAUT"*/
			(void) fprintf(fd, "%s", buf);
		}
		(void) fprintf(fd, "\n");
	}
}

static void decritretraites(FILE *fd, _PAYS *pays, BOOL affpays) {
	_RETRAITE *p, *prec;
	SPECIFICITE specif;
	char buf[TAILLEMESSAGE];
	char trigramme[TAILLEMOT];

	for (p = RETRAITE.t; p < RETRAITE.t + RETRAITE.n; p++)
		if (p->delogee->unite->pays == pays)
			break;
	if (p == RETRAITE.t + RETRAITE.n)
		return;

	if (affpays)
		(void) fprintf(fd, "%s\n", pays->nom);

	(void) strcpy(trigramme, "");

	for (;;) {

		prec = NULL;

		for (p = RETRAITE.t; p < RETRAITE.t + RETRAITE.n; p++) {

			if (p->delogee->unite->pays != pays)
				continue;

			if (strcmp(p->delogee->unite->zonedepart->region->nom, trigramme)
					<= 0)
				continue;

			if (prec == NULL || strcmp(
					p->delogee->unite->zonedepart->region->nom,
					prec->delogee->unite->zonedepart->region->nom) < 0)
				prec = p;
		}

		/* Si on a pas trouve on arrete tout */
		if (prec == NULL) {
			(void) fprintf(fd, "\n");
			break;
		}

		p = prec;
		(void) strcpy(trigramme, p->delogee->unite->zonedepart->region->nom);

		(void) strcpy(specif, p->delogee->unite->zonedepart->specificite);
		Strlwr(specif);
		(void) fprintf(fd, "%s %s%s",
				(p->delogee->unite->typeunite == ARMEE ? "A" : "F"),
				p->delogee->unite->zonedepart->region->nom, specif);

		switch (p->typeretraite) {

		case FUITE:
			(void) strcpy(specif, p->zonedest->specificite);
			Strlwr(specif);
			(void) fprintf(fd, " %c %s%s", (p->valable ? 'R' : 'r'),
					p->zonedest->region->nom, specif);
			if (!p->valable) {
				cherchechaine(__FILE__, 21, buf, 0); /*"(a)"*/
				(void) fprintf(fd, "%s", buf);
			}
			break;

		case SUICIDE:
			(void) fprintf(fd, " A");
			break;

		}

		if (p->noligne == 0) {
			cherchechaine(__FILE__, 20, buf, 0); /*";PAR DEFAUT"*/
			(void) fprintf(fd, "%s", buf);
		}
		(void) fprintf(fd, "\n");
	}
}

static void decritajustements(FILE *fd, _PAYS *pays, BOOL affpays) {
	_AJUSTEMENT *p;
	SPECIFICITE specif;
	char buf[TAILLEMESSAGE];

	for (p = AJUSTEMENT.t; p < AJUSTEMENT.t + AJUSTEMENT.n; p++)
		if (p->unite->pays == pays)
			break;
	if (p == AJUSTEMENT.t + AJUSTEMENT.n)
		return;

	if (affpays)
		(void) fprintf(fd, "%s\n", pays->nom);

	for (p = AJUSTEMENT.t; p < AJUSTEMENT.t + AJUSTEMENT.n; p++)
		if (p->unite->pays == pays) {
			switch (p->typeajustement) {

			case AJOUTE:
				(void) fprintf(fd, "+ ");
				break;

			case SUPPRIME:
				(void) fprintf(fd, "- ");
				break;

			}

			(void) strcpy(specif, p->unite->zonedepart->specificite);
			Strlwr(specif);
			(void) fprintf(fd, "%s %s%s", (p->unite->typeunite == ARMEE ? "A"
					: "F"), p->unite->zonedepart->region->nom, specif);

			if (p->noligne == 0) {
				cherchechaine(__FILE__, 20, buf, 0); /*";PAR DEFAUT"*/
				(void) fprintf(fd, "%s", buf);
			}
			(void) fprintf(fd, "\n");
		}

	(void) fprintf(fd, "\n");
}

static void decritpossessions(FILE *fd, _PAYS *pays, BOOL affpays) {
	_POSSESSION *p, *q;
	int ncentres, ncentresavant;
	BOOL premier, premieremodif;

	ncentres = 0;
	for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++) {
		if (p->pays == pays)
			ncentres++;
	}
	ncentresavant = 0;
	for (p = POSSESSIONAVANT.t; p < POSSESSIONAVANT.t + POSSESSIONAVANT.n; p++) {
		if (p->pays == pays)
			ncentresavant++;
	}

	if (ncentres == 0 && ncentresavant == 0)
		return;

	if (affpays)
		(void) fprintf(fd, "%s: ", pays->nom);

	premier = TRUE;
	for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++)
		if (p->pays == pays) {
			if (!premier)
				(void) fprintf(fd, " ");
			(void) fprintf(fd, "%s", p->centre->region->nom);
			premier = FALSE;
		}

	premieremodif = TRUE;
	for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++)
		if (p->pays == pays) {
			/* les nouveaux */
			for (q = POSSESSIONAVANT.t; q < POSSESSIONAVANT.t
					+ POSSESSIONAVANT.n; q++)
				if (q->pays == p->pays && q->centre == p->centre)
					break;
			if (q == POSSESSIONAVANT.t + POSSESSIONAVANT.n) {
				if (premieremodif) {
					(void) fprintf(fd, " (");
					premier = TRUE;
				}
				premieremodif = FALSE;
				if (!premier)
					(void) fprintf(fd, " ");
				premier = FALSE;
				(void) fprintf(fd, "+%s", p->centre->region->nom);
			}
		}
	for (p = POSSESSIONAVANT.t; p < POSSESSIONAVANT.t + POSSESSIONAVANT.n; p++)
		if (p->pays == pays) {
			/* les perdus */
			for (q = POSSESSION.t; q < POSSESSION.t + POSSESSION.n; q++) {
				if (q->centre != p->centre)
					continue;
				if (q->pays == p->pays)
					continue;
				if (premieremodif) {
					(void) fprintf(fd, " (");
					premier = TRUE;
				}
				premieremodif = FALSE;
				if (!premier)
					(void) fprintf(fd, " ");
				premier = FALSE;
				(void) fprintf(fd, "-%s", p->centre->region->nom);
			}
		}
	if (!premieremodif)
		(void) fprintf(fd, ")");

	(void) fprintf(fd, "\n");
}

void decritordres(char *nomfic, BOOL affpays)
/* Decrit les ordres passes */
{
	FILE *fd;
	_PAYS *p;
	char buf[TAILLEMESSAGE];

	if (!strcmp(nomfic, ""))
		return;

	if ((fd = fopen(nomfic, "w")) == NULL) {
		cherchechaine(__FILE__, 23, buf, 1, nomfic); /*"Impossible d'ecrire archivage ordres : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	switch ((IDSAISON) (SAISON % NSAISONS)) {

	case PRINTEMPS:
	case AUTOMNE:
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
			decritmouvements(fd, p, affpays);
		break;

	case BILAN:
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
			decritajustements(fd, p, affpays);
		break;

	case ETE:
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
			decritretraites(fd, p, affpays);
		break;

	case HIVER:
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
			decritretraites(fd, p, affpays);
		(void) fprintf(fd, "\n");
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
			decritpossessions(fd, p, affpays);
		fprintf(fd, "\n");
		infospreajustements(fd);
		break;
	}



	(void) fclose(fd);
}

static void classeunites(TUNITE unite, INDEXUNITE indexunite) {
	_UNITE *p;
	char *nom, *nomrec, *nomcour;
	int i, n, nrec;

	nrec = 0; /* Evite un avertissement du compilateur */
	nomcour = NULL;

	for (i = 0; i < unite.n; i++) {

		nomrec = NULL;
		for (n = 0, p = unite.t; p < unite.t + unite.n; n++, p++) {
			nom = p->zone->region->nom;
			if ((nomrec == NULL || strcmp(nom, nomrec) < 0) && (nomcour == NULL
					|| strcmp(nom, nomcour) > 0)) {
				nomrec = nom;
				nrec = n;
			}
		}

		nomcour = nomrec;
		indexunite[i] = nrec;

	}
}

static void classedelogees(TDELOGEE delogee, INDEXDELOGEE indexdelogee) {
	_DELOGEE *p;
	char *nom, *nomrec, *nomcour;
	int i, n, nrec;

	nomcour = NULL;
	nrec = 0; /* Evite un avertissement du compilateur */

	for (i = 0; i < delogee.n; i++) {

		nomrec = NULL;
		for (n = 0, p = delogee.t; p < delogee.t + delogee.n; n++, p++) {
			nom = p->unite->zone->region->nom;
			if ((nomrec == NULL || strcmp(nom, nomrec) < 0) && (nomcour == NULL
					|| strcmp(nom, nomcour) > 0)) {
				nomrec = nom;
				nrec = n;
			}
		}

		nomcour = nomrec;
		indexdelogee[i] = nrec;

	}
}

void decritprototypes(char *nomfic, _PAYS *pays)
/* Prototypes des ordres pour les joueurs avec slt les unites */
{
	FILE *fd;
	int i, n, souhaites, nunit, ncent, najustementsposs;
	SPECIFICITE specif;
	_UNITE *p;
	_DELOGEE *q;
	INDEXUNITE indexunite;
	INDEXDELOGEE indexdelogee;
	char buf[TAILLEMESSAGE];

	if (!strcmp(nomfic, ""))
		return;

	if ((fd = fopen(nomfic, "w")) == NULL) {
		cherchechaine(__FILE__, 26, buf, 1, nomfic); /*"Impossible d'ouvrir le fichier pour prototypes: %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	switch ((IDSAISON) (SAISON % NSAISONS)) {

	case PRINTEMPS:
	case AUTOMNE:
		n = 0;
		classeunites(UNITE, indexunite);
		for (i = 0; i < UNITE.n; i++) {
			p = UNITE.t + indexunite[i];
			if (p->pays == pays) {
				n++;
				(void) strcpy(specif, p->zonedepart->specificite);
				Strlwr(specif);
				(void) fprintf(fd, "%s %s%s\n", (p->typeunite == ARMEE ? "A"
						: "F"), p->zonedepart->region->nom, specif);
			}
		}
		if (n == 0) {
			cherchechaine(__FILE__, 27, buf, 0); /*";Pas de mouvement a prevoir"*/
			(void) fprintf(fd, "%s\n", buf);
		}
		break;

	case ETE:
	case HIVER:
		n = 0;
		classedelogees(DELOGEE, indexdelogee);
		for (i = 0; i < DELOGEE.n; i++) {
			q = DELOGEE.t + indexdelogee[i];
			if (q->unite->pays == pays) {
				n++;
				(void) strcpy(specif, q->unite->zonedepart->specificite);
				Strlwr(specif);
				(void) fprintf(fd, "%s %s%s R\n",
						(q->unite->typeunite == ARMEE ? "A" : "F"),
						q->unite->zonedepart->region->nom, specif);
			}
		}
		if (n == 0) {
			cherchechaine(__FILE__, 28, buf, 0); /*";Pas de retraite a prevoir"*/
			(void) fprintf(fd, "%s\n", buf);
		}
		break;

	case BILAN:
		calculajustements(pays, &ncent, &nunit, &najustementsposs);
		souhaites = INF(ncent - nunit,najustementsposs);

		if (souhaites == 0) {
			cherchechaine(__FILE__, 29, buf, 0); /*";Aucun ajustement a prevoir"*/
			(void) fprintf(fd, "%s\n", buf);
		} else if (souhaites == -nunit) {
			cherchechaine(__FILE__, 30, buf, 0); /*";Suppression toutes unites"*/
			(void) fprintf(fd, "%s\n\n", buf);
			for (p = UNITE.t; p < UNITE.t + UNITE.n; p++)
				if (p->pays == pays) {
					(void) strcpy(specif, p->zone->specificite);
					Strlwr(specif);
					(void) fprintf(fd, "- %s %s%s\n",
							(p->typeunite == ARMEE ? "A" : "F"),
							p->zone->region->nom, specif);
				}
		} else {
			if (souhaites > 0) {
				cherchechaine(__FILE__, 31, buf, 0); /*";Indiquez les unites a ajouter (une par ligne apres chaque '+')"*/
				(void) fprintf(fd, "%s\n\n", buf);
			}
			if (souhaites < 0) {
				cherchechaine(__FILE__, 32, buf, 0); /*";Indiquez les unites a supprimer (une par ligne apres chaque '-')"*/
				(void) fprintf(fd, "%s\n\n", buf);
			}
			for (i = 1; i <= abs(souhaites); i++) {
				if (souhaites > 0)
					(void) fprintf(fd, "+ \n");
				if (souhaites < 0)
					(void) fprintf(fd, "- \n");
			}
		}
		break;

	}

	(void) fclose(fd);
}

void decritordressecurite(char *nomfic, _PAYS *pays)
/* Des ordres valides pour les joueurs (les ordres les plus simples) */
{
	_SUPPRESSIONS SUPPRESSIONS;
	FILE *fd;
	int ajustements, el, elrec, souhaites, nunit, ncent, najustementsposs;
	SPECIFICITE specif;
	_UNITE **w, *p, *prec;
	_DELOGEE *q;
	char buf[TAILLEMESSAGE];

	if (!strcmp(nomfic, ""))
		return;

	if ((fd = fopen(nomfic, "w")) == NULL) {
		cherchechaine(__FILE__, 33, buf, 1, nomfic); /*"Impossible d'ouvrir le fichier pour ordres securite : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	switch ((IDSAISON) (SAISON % NSAISONS)) {

	case PRINTEMPS:
	case AUTOMNE:

		for (p = UNITE.t; p < UNITE.t + UNITE.n; p++)
			if (p->pays == pays) {
				(void) strcpy(specif, p->zonedepart->specificite);
				Strlwr(specif);
				(void) fprintf(fd, "%s %s%s H\n", (p->typeunite == ARMEE ? "A"
						: "F"), p->zonedepart->region->nom, specif);
			}
		break;

	case ETE:
	case HIVER:

		for (q = DELOGEE.t; q < DELOGEE.t + DELOGEE.n; q++)
			if (q->unite->pays == pays) {
				(void) strcpy(specif, q->unite->zonedepart->specificite);
				Strlwr(specif);
				(void) fprintf(fd, "%s %s%s A\n",
						(q->unite->typeunite == ARMEE ? "A" : "F"),
						q->unite->zonedepart->region->nom, specif);
			}
		break;

	case BILAN:

		calculajustements(pays, &ncent, &nunit, &najustementsposs);
		souhaites = INF(ncent - nunit,najustementsposs);

		SUPPRESSIONS.n = 0;
		ajustements = 0;
		while (ajustements > souhaites) {

			prec = NULL;
			for (p = UNITE.t; p < UNITE.t + UNITE.n; p++) {

				if (p->pays != pays)
					continue;

				for (w = SUPPRESSIONS.t; w < SUPPRESSIONS.t + SUPPRESSIONS.n; w++)
					if (*w == p)
						break;
				/* Deja pris cette unite */
				if (w != SUPPRESSIONS.t + SUPPRESSIONS.n)
					continue;

				if (prec == NULL) {
					prec = p;
					continue;
				}

				el = eloignement(p->typeunite, p->zone, pays);
				elrec = eloignement(prec->typeunite, prec->zone, pays);

				/* Si c'est plus proche */
				if (el > elrec) {
					prec = p;
					continue;
				}

				if (el == elrec) {

					/* Si c'est  une flotte et l'autre une armee */
					if (p->typeunite == FLOTTE && prec->typeunite == ARMEE) {
						prec = p;
						continue;
					}

					/* S'il est avant dans l'ordre alphabétique il passe devant */
					if (strcmp(p->zone->region->nom, prec->zone->region->nom)
							< 0) {
						prec = p;
						continue;
					}
				}
			}

			(void) strcpy(specif, prec->zone->specificite);
			Strlwr(specif);
			(void) fprintf(fd, "- %s %s%s\n", (prec->typeunite == ARMEE ? "A"
					: "F"), prec->zone->region->nom, specif);

			SUPPRESSIONS.t[SUPPRESSIONS.n++] = prec;
			ajustements--;
		}
		break;
	}

	(void) fclose(fd);
}

void decritordrescomplets(char *nomfic, _PAYS *pays, BOOL affpays)
/* Retrouve les ordres d'un joueur */
{
	FILE *fd;
	char buf[TAILLEMESSAGE];

	if (!strcmp(nomfic, ""))
		return;

	if ((fd = fopen(nomfic, "w")) == NULL) {
		cherchechaine(__FILE__, 37, buf, 1, nomfic); /*"Impossible d'ecrire ordres reconstitues : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	switch ((IDSAISON) (SAISON % NSAISONS)) {

	case PRINTEMPS:
	case AUTOMNE:
		decritmouvements(fd, pays, affpays);
		break;

	case BILAN:
		decritajustements(fd, pays, affpays);
		break;

	case ETE:
	case HIVER:
		decritretraites(fd, pays, affpays);
		break;
	}

	(void) fclose(fd);
}

void decritactifs(char *nomfic)
/* Liste des pays actifs */
{
	FILE *fd;
	_PAYS *p;
	_UNITE *q;
	_DELOGEE *r;
	int ncentres, nunites, najustementspossibles;
	char buf[TAILLEMESSAGE];

	if (!strcmp(nomfic, ""))
		return;

	if ((fd = fopen(nomfic, "w")) == NULL) {
		cherchechaine(__FILE__, 42, buf, 1, nomfic); /*"Impossible d'ouvrir le fichier pour pays actifs : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	switch ((IDSAISON) (SAISON % NSAISONS)) {

	case PRINTEMPS:
	case AUTOMNE:
		/* Actif si une unite presente du pays */
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
			for (q = UNITE.t; q < UNITE.t + UNITE.n; q++)
				if (q->pays == p) {
					(void) fprintf(fd, "%s ", p->nom);
					q = UNITE.t + UNITE.n;
				}
		(void) fprintf(fd, "\n");
		break;

	case ETE:
	case HIVER:
		/* Actif si une unite delogee mais non aneantie presente du pays */
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++)
			for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
				if (!uniteaneantie(r->unite) && (r->unite->pays == p)) {
					(void) fprintf(fd, "%s ", p->nom);
					r = DELOGEE.t + DELOGEE.n;
				}
		(void) fprintf(fd, "\n");
		break;

	case BILAN:
		for (p = PAYS.t; p < PAYS.t + PAYS.n; p++) {
			/* Compte tout */
			calculajustements(p, &ncentres, &nunites, &najustementspossibles);
			if ((nunites > ncentres) || ((nunites < ncentres)
					&& (najustementspossibles > 0)))
				(void) fprintf(fd, "%s ", p->nom);
		}
		(void) fprintf(fd, "\n");
		break;

	}

	(void) fclose(fd);
}

void decritvivants(char *nomfic)
/* Liste des pays vivants */
{
	FILE *fd;
	_PAYS *p;
	int ncentres, nunites, najustementspossibles;
	char buf[TAILLEMESSAGE];

	if (!strcmp(nomfic, ""))
		return;

	if ((fd = fopen(nomfic, "w")) == NULL) {
		cherchechaine(__FILE__, 43, buf, 1, nomfic); /*"Impossible d'ouvrir le fichier pour pays vivants : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++) {

		/* Compte tout */
		calculajustements(p, &ncentres, &nunites, &najustementspossibles);

		/* Vivant si a un centre ou une unite */
		if (nunites > 0 || ncentres > 0)
			(void) fprintf(fd, "%s ", p->nom);
	}
	(void) fprintf(fd, "\n");

	(void) fclose(fd);
}

void infospreajustements(FILE *fd)
{
	_PAYS **p;
	int nappr, ncent, nunit, najustementsposs;
	char buf[TAILLENOMFIC];

	classementpays();

	for (p = PAYSCLASSES.t; p < PAYSCLASSES.t + PAYSCLASSES.n; p++) {

		calculajustements(*p, &ncent, &nunit, &najustementsposs);

		nappr = INF(najustementsposs, ncent - nunit);

		/* le gars construit */
		if (nappr > 0) {
			sprintf(buf, "%s: %d centres, %d unités, %d emplacements : %d construction(s)", (*p)->nom, ncent, nunit, najustementsposs, nappr);
		}
		/* le gars detruit */
		else if (nappr < 0) {
			sprintf(buf, "%s: %d centres, %d unités : %d suppression(s)", (*p)->nom, ncent, nunit, abs(nappr));
		}
		/* le gars fait rien */
		else
		{
			sprintf(buf, "%s: %d centres, %d unités", (*p)->nom, ncent, nunit);
		}
		(void) fprintf(fd, "%s\n", buf);
	}
}
