#include "../solveur/define.h"
#include "define2.h"
#include "../solveur/struct.h"
#include "../solveur/includes.h"
#include "../solveur/protos.h"
#include "protos2.h"
#include "../solveur/datas.h"


typedef enum {
	MOUVINIT = 1100,
	MOUV0,
	MOUV1,
	MOUV2,
	MOUV3,
	MOUV4,
	MOUV5,
	MOUV6,
	MOUV7,
	MOUV8,
	MOUV9,
	MOUVFIN
} ETATAUTOMOUV;

typedef enum {
	UNITINIT = 1200, UNIT0, UNIT1, UNIT2, UNIT3, UNITFIN
} ETATAUTOUNIT;

typedef enum {
	CENTINIT = 1300, CENT0, CENT1, CENT2, CENTFIN
} ETATAUTOCENT;

static void verifordres(int);
static void verifunites(int);
static void verifcentres(int);

/* Ces infos seront exploitees dans la procedure erreurparse() si elle est appellee */
extern char image[TAILLEMESSAGE];
extern int lecture;
extern int noligne;

/*********************************************************************************/
/*                          ROUTINES DU PARSEUR                                  */
/*********************************************************************************/

/************************* PARTIE BLINDEE ***************************/
static void verifordres(int nordres) {
	char buf[TAILLEMESSAGE * 2], bufn[TAILLEENTIER];

	if (nordres > NORDRESTHEORIQUE) {
		(void) sprintf(bufn, "%d", nordres);
		cherchechaine(__FILE__, 1, buf, 1, bufn); /*"Plus d'ordres que le nombre theorique (%1)"*/
		erreurparse(NULL, LESREGLES, FALSE, buf);
	}
}

static void verifunites(int nunites) {
	char buf[TAILLEMESSAGE * 2], bufn[TAILLEENTIER];

	if (nunites > NUNITESTHEORIQUE) {
		(void) sprintf(bufn, "%d", nunites);
		cherchechaine(__FILE__, 2, buf, 1, bufn); /*"Plus d'unite que le nombre theorique (%1)"*/
		erreurparse(NULL, LESREGLES, FALSE, buf);
	}
	if (nunites < NUNITESTHEORIQUE) {
		(void) sprintf(bufn, "%d", nunites);
		cherchechaine(__FILE__, 3, buf, 1, bufn); /*"Moins d'unite que le nombre theorique (%1)"*/
		avertir(buf);
	}
}

static void verifcentres(int ncentres) {
	char buf[TAILLEMESSAGE * 2], bufn[TAILLEENTIER];

	if (ncentres > NORDRESTHEORIQUE) {
		(void) sprintf(bufn, "%d", ncentres);
		cherchechaine(__FILE__, 4, buf, 1, bufn); /*"Plus de centres possedes que le nombre theorique (%1)"*/
		erreurparse(NULL, LESREGLES, FALSE, buf);
	}
	if (ncentres < NORDRESTHEORIQUE) {
		(void) sprintf(bufn, "%d", ncentres);
		cherchechaine(__FILE__, 5, buf, 1, bufn); /*"Moins de centres possedes que le nombre theorique (%1)"*/
		avertir(buf);
	}
}

/********************************************************************/

void verifglobale(IDSAISON saison) {
	_PAYS *p;
	_CENTREDEPART *q;
	_POSSESSION *r;
	_UNITE *u;
	char buf[TAILLEMESSAGE * 2];

	int ncentres, nunites;

	/* Conformité entre nombre d'unites et de centres */
	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++) {
		ncentres = 0;
		for (r = POSSESSION.t; r < POSSESSION.t + POSSESSION.n; r++)
			if (r->pays == p)
				ncentres++;
		nunites = 0;
		for (u = UNITE.t; u < UNITE.t + UNITE.n; u++)
			if (u->pays == p)
				nunites++;
		/* Pas plus d'unites que de centres */
		if (nunites > ncentres && ncentres > 0) {
			cherchechaine(__FILE__, 52, buf, 1, p->nom); /*"Pays %1 : plus d'unites que de centres (et au moins un centre)"*/
			switch (saison) {
			case PRINTEMPS:
				erreurverif(NULL, ENTREE, buf);
				break;
			default:
				avertir(buf);
				break;
			}
		}
		/* Avertisement si plus  de centres que d'unites et un centre national libre*/
		if (ncentres > nunites) {
			for (q = CENTREDEPART.t; q < CENTREDEPART.t + CENTREDEPART.n; q++)
				if (q->pays == p && chercheoccupant(q->centre->region) == NULL)
					break;
			if (q < CENTREDEPART.t + CENTREDEPART.n) {
				cherchechaine(__FILE__, 53, buf, 1, p->nom); /*"Pays %1 : plus de centres que d'unités au printemps (et au moins un centre national libre)"*/
				avertir(buf);
			}
		}
	}

	/* Si une unite occupe un centre le proprietaire de l'unite a aussi le centre */
	for (u = UNITE.t; u < UNITE.t + UNITE.n; u++) {
		for (r = POSSESSION.t; r < POSSESSION.t + POSSESSION.n; r++)
			if (u->zone->region == r->centre->region && r->pays != u->pays) {
				cherchechaine(__FILE__, 54, buf, 1, r->centre->region->nom); /*"Unite %1 : son pays ne possede pas le centre"*/
				switch (saison) {
				case PRINTEMPS:
					erreurverif(NULL, ENTREE, buf);
					break;
				default:
					avertir(buf);
					break;
				}
			}
	}
}
void parsemouvements2(char *nomfic) {
	FILE *fd;
	TOKEN tok;
	ETATAUTOMOUV etat;
	char buf[TAILLEMESSAGE * 2], nomunite[2 * TAILLEMOT],
			nomzone[TAILLEMOT * 2], nomzone2[TAILLEMOT * 2];
	_COTEPOSS *p;
	TYPEUNITE typeunite;
	_ZONE *zonedest, *zonedest2, *zonedest3, *zoneunite, *zonepossible;
	_PAYS *pays;
	int ordrespays;
	int nordres;
	BOOL coteatrouver;

	if ((fd = fopen(nomfic, "r")) == NULL) {
		cherchechaine(__FILE__, 6, buf, 1, nomfic); /*"Impossible de lire les ordres de mouvement : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	zoneunite = NULL; /* Evite un avertissement du compilateur */
	zonepossible = NULL; /* Evite un avertissement du compilateur */

	pays = NULL;
	lecture = ORDRES;
	(void) strcpy(image, "");
	noligne = 1;
	coteatrouver = FALSE;

	etat = MOUVINIT;

	typeunite = -1; /* Evite un avertissement du compilateur */
	ordrespays = -1; /* Evite un avertissement du compilateur */
	nordres = 0;

	for (;;) {
		gettoken(fd, &tok);
		switch (etat) {

		case MOUVINIT:
			switch (tok.id) {
			case FINFICHIER:
				cherchechaine(__FILE__, 7, buf, 0); /*"Pas d'ordre de mouvement dans le fichier"*/
				avertir(buf);
				(void) fclose(fd);
				verifordres(nordres);
				return;
			case FINLIGNE:
				continue;
			case CHAINE:
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 8, buf, 1, tok.val); /*"Pays %1 inconnu"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				ordrespays = 0;
				etat = MOUV9;
				break;
			default:
				cherchechaine(__FILE__, 9, buf, 0); /*"Nom de pays attendu "*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case MOUV9:
			if (tok.id != FINLIGNE) {
				cherchechaine(__FILE__, 47, buf, 0); /*"Aller a la ligne apres le nom de pays"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			ungettoken(&tok);
			etat = MOUV0;
			break;

		case MOUV0:
			switch (tok.id) {
			case FINLIGNE:
				continue;
			case FINFICHIER:
				if (ordrespays == 0) {
					cherchechaine(__FILE__, 10, buf, 1, pays->nom); /*"Pays %1 declare mais sans ordres"*/
					avertir(buf);
				}
				(void) fclose(fd);
				verifordres(nordres);
				return;
			case UNEARMEESUICIDE:
				typeunite = ARMEE;
				etat = MOUV1;
				break;
			case UNEFLOTTE:
				typeunite = FLOTTE;
				etat = MOUV1;
				break;
			case CHAINE:
				if (ordrespays == 0) {
					cherchechaine(__FILE__, 11, buf, 1, pays->nom); /*"Pays %1 declare mais sans ordres"*/
					avertir(buf);
				}
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 12, buf, 1, tok.val); /*"Pays %1 inconnu"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				ordrespays = 0;
				break;
			default:
				cherchechaine(__FILE__, 13, buf, 0); /*"Type d'unite 'A' ou 'F' ou nom de pays attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case MOUV1:
			if (tok.id != CHAINE) {
				cherchechaine(__FILE__, 14, buf, 0); /*"Zone de l'unite active attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			(void) strcpy(nomzone, tok.val);
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
			case UNSLASH:
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNECOTEEST:
			case UNECOTEOUEST:
			case UNECOTENORD:
			case UNECOTESUD:
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				break;
			default:
				ungettoken(&tok);
			}
			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 16, buf, 1, nomzone); /*"Zone %1 inconnue"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			if (!compatibles(typeunite, zonedest)) {
				if(typeunite == ARMEE) {
					cherchechaine(__FILE__, 17, buf, 0); /*"Une telle unite ne peut se trouver a cet endroit"*/
					erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
				} else {
					cherchechaine(__FILE__, 55, buf, 0); /*"Va falloir deviner la côte"*/
					avertir(buf);
					coteatrouver = TRUE; /* indicateur qu'on cherche la cote */
					zoneunite = zonedest; /* position de l'unite en partie */
				}
			}

			(void) strcpy(nomunite, zonedest->region->nom);
			(void) strcat(nomunite, zonedest->specificite);
			(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));

			if (chercheunite(nomunite) != NULL) {
				cherchechaine(__FILE__, 18, buf, 1, nomunite); /*"Unite %1 apparaissant deux fois"*/
				erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
			}

			if (chercheoccupant(zonedest->region) != NULL) {
				cherchechaine(__FILE__, 19, buf, 1, tok.val); /*"Il y a deja une unite en region %1"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			if(!coteatrouver) { /* trouvee directement */

				UNITE.t[UNITE.n].typeunite = typeunite;
				UNITE.t[UNITE.n].pays = pays;
				UNITE.t[UNITE.n].zone = zonedest;
				UNITE.t[UNITE.n].zonedepart = UNITE.t[UNITE.n].zone;
				assert(++UNITE.n != NUNITES);
			}

			etat = MOUV2;
			break;

		case MOUV2:
			switch (tok.id) {
			case UNSTAND:
				if(coteatrouver) {
					/* On va essayer de trouver la cote quand meme */
					/* la premiere cote trouvee qui existe */
					for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
						(void) strcpy(nomzone, zoneunite->region->nom);
						(void) strcat(nomzone, p->nom);
						if ((zonedest3 = cherchezone(nomzone)) != NULL) {
							zonepossible = zonedest3;
							break;
						}
					}
				}
				etat = MOUVFIN;
				break;
			case UNEATTAQUESUPPRESSION:
			case UNSOUTIEN:
			case UNCONVOI:
				if(coteatrouver) {
					(void) strcpy(nomzone2, "");
				}
				etat = MOUV3;
				break;
			default:
				cherchechaine(__FILE__, 20, buf, 0); /*"Ordre unite active '-' 'T' 'S' ou 'C' attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case MOUV3:
			switch (tok.id) {
			case FINLIGNE:
			case FINFICHIER:
				ungettoken(&tok);
				etat = MOUVFIN;
				break;
			default:
				if(coteatrouver) {
					switch (tok.id) {
					case CHAINE:
						(void) strcpy(nomzone2, tok.val);
						break;
					case UNECOTEEST:
					case UNECOTEOUEST:
					case UNECOTENORD:
					case UNECOTESUD:
						(void) strcat(nomzone2, tok.val);
						break;
					default:
						(void) strcpy(nomzone2, "");
						break;
					}
					if (strcmp(nomzone2,"") && (zonedest2 = cherchezone(nomzone2)) != NULL) {
						/* On va essayer de trouver la cote quand meme */
						/* la premiere cote trouvee qui peut etre voisine de ce qu'on voit */
						for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
							(void) strcpy(nomzone, zoneunite->region->nom);
							(void) strcat(nomzone, p->nom);
							if (((zonedest3 = cherchezone(nomzone)) != NULL) &&
									flottevoisin(zonedest3, zonedest2)) {
								zonepossible = zonedest3;
								break;
							}
						}
					}
				}

				etat = MOUV3;
			}
			break;

		case MOUVFIN:
			if (tok.id != FINLIGNE && tok.id != FINFICHIER) {
				cherchechaine(__FILE__, 21, buf, 0); /*"Ordre de mouvement trop long, utiliser ';'"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			if(coteatrouver) {
				if(zonepossible != NULL) {
					UNITE.t[UNITE.n].typeunite = typeunite;
					UNITE.t[UNITE.n].pays = pays;
					UNITE.t[UNITE.n].zone = zonepossible;
					UNITE.t[UNITE.n].zonedepart = UNITE.t[UNITE.n].zone;
					assert(++UNITE.n != NUNITES);
				} else {
					cherchechaine(__FILE__, 21, buf, 0); /*"Impossible de deviner la cote"*/
					erreurparse(pays, SYNTAXIQUE, FALSE, buf);
				}
				coteatrouver = FALSE; /* important : on cherche plus les cotes */
			}
			ordrespays++;
			nordres++;
			etat = MOUV0;
			break;

		default:
			assert(FALSE); /* Devrait pas passer ici */
		}
	}
}

void parseunites2(char *nomfic) {
	FILE *fd;
	TOKEN tok;
	ETATAUTOUNIT etat;
	char buf[TAILLEMESSAGE * 2], nomunite[2 * TAILLEMOT],
			nomzone[TAILLEMOT * 2];

	TYPEUNITE typeunite;
	_ZONE *zonedest;
	_PAYS *pays;
	int unitespays;
	int nunites;

	if ((fd = fopen(nomfic, "r")) == NULL) {
		cherchechaine(__FILE__, 22, buf, 1, nomfic); /*"Impossible de lire les positions des unites : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	pays = NULL;
	lecture = UNITES;
	(void) strcpy(image, "");
	noligne = 1;

	etat = UNITINIT;

	typeunite = -1; /* Evite un avertissement du compilateur */
	unitespays = -1; /* Evite un avertissement du compilateur */
	nunites = 0;

	for (;;) {
		gettoken(fd, &tok);
		switch (etat) {

		case UNITINIT:
			switch (tok.id) {
			case FINFICHIER:
				cherchechaine(__FILE__, 23, buf, 0); /*"Pas d'ordre de mouvement dans le fichier"*/
				avertir(buf);
				(void) fclose(fd);
				verifunites(nunites);
				return;
			case FINLIGNE:
				continue;
			case CHAINE:
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 24, buf, 1, tok.val); /*"Pays %1 inconnu"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				unitespays = 0;
				etat = UNIT3;
				break;
			default:
				cherchechaine(__FILE__, 25, buf, 0); /*"Nom de pays attendu "*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case UNIT3:
			if (tok.id != FINLIGNE) {
				cherchechaine(__FILE__, 47, buf, 0); /*"Aller a la ligne apres le nom de pays"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			etat = UNIT0;
			ungettoken(&tok);
			break;

		case UNIT0:
			switch (tok.id) {
			case FINLIGNE:
				continue;
			case FINFICHIER:
				if (unitespays == 0) {
					cherchechaine(__FILE__, 26, buf, 1, pays->nom); /*"Pays %1 declare mais sans unite"*/
					avertir(buf);
				}
				(void) fclose(fd);
				verifunites(nunites);
				return;
			case UNEARMEESUICIDE:
				typeunite = ARMEE;
				etat = UNIT1;
				break;
			case UNEFLOTTE:
				typeunite = FLOTTE;
				etat = UNIT1;
				break;
			case CHAINE:
				if (unitespays == 0) {
					cherchechaine(__FILE__, 27, buf, 1, pays->nom); /*"Pays %1 declare mais sans unite"*/
					avertir(buf);
				}
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 28, buf, 1, tok.val); /*"Pays %1 inconnu"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				unitespays = 0;
				break;
			default:
				cherchechaine(__FILE__, 29, buf, 0); /*"Type d'unite 'A' ou 'F' ou nom de pays attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case UNIT1:
			if (tok.id != CHAINE) {
				cherchechaine(__FILE__, 30, buf, 0); /*"Zone de l'unite active attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			(void) strcpy(nomzone, tok.val);
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
			case UNSLASH:
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNECOTEEST:
			case UNECOTEOUEST:
			case UNECOTENORD:
			case UNECOTESUD:
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				break;
			default:
				ungettoken(&tok);
			}
			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 32, buf, 1, tok.val); /*"Zone %1 inconnue"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			if (!compatibles(typeunite, zonedest)) {
				cherchechaine(__FILE__, 33, buf, 0); /*"Une telle unite ne peut se trouver a cet endroit"*/
				erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
			}

			(void) strcpy(nomunite, zonedest->region->nom);
			(void) strcat(nomunite, zonedest->specificite);
			(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));

			if (chercheunite(nomunite) != NULL) {
				cherchechaine(__FILE__, 34, buf, 1, nomunite); /*"Unite %1 apparaissant deux fois"*/
				erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
			}

			if (chercheoccupant(zonedest->region) != NULL) {
				cherchechaine(__FILE__, 35, buf, 1, tok.val); /*"Il y a deja une unite en region %1"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			UNITE.t[UNITE.n].typeunite = typeunite;
			UNITE.t[UNITE.n].pays = pays;
			UNITE.t[UNITE.n].zone = zonedest;
			UNITE.t[UNITE.n].zonedepart = UNITE.t[UNITE.n].zone;

			assert(++UNITE.n != NUNITES);

			etat = UNITFIN;
			break;

		case UNITFIN:
			if (tok.id != FINLIGNE && tok.id != FINFICHIER) {
				cherchechaine(__FILE__, 36, buf, 0); /*"Placement d'unite trop long, utiliser ';'"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			unitespays++;
			nunites++;
			etat = UNIT0;
			break;

		default:
			assert(FALSE); /* Devrait pas passer ici */
		}
	}
}

void parsecentres2(char *nomfic) {
	FILE *fd;
	TOKEN tok;
	ETATAUTOCENT etat;
	char buf[TAILLEMESSAGE * 2];

	_PAYS *pays;
	_CENTRE *centre;
	int centrespays;
	int ncentres;

	if ((fd = fopen(nomfic, "r")) == NULL) {
		cherchechaine(__FILE__, 37, buf, 1, nomfic); /*"Impossible de lire les centres possedes : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	pays = NULL;
	lecture = CENTRES;
	(void) strcpy(image, "");
	noligne = 1;

	etat = CENTINIT;

	centrespays = -1; /* Evite un avertissement du compilateur */
	ncentres = 0;

	for (;;) {
		gettoken(fd, &tok);
		switch (etat) {

		case CENTINIT:
			switch (tok.id) {
			case FINFICHIER:
				if (ncentres == 0) {
					cherchechaine(__FILE__, 38, buf, 0); /*"Pas de possessions de centres dans le fichier"*/
					avertir(buf);
				}
				(void) fclose(fd);
				verifcentres(ncentres);
				return;
			case FINLIGNE:
				continue;
			case CHAINE:
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 39, buf, 1, tok.val); /*"Pays %1 inconnu"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				centrespays = 0;
				etat = CENT2;
				break;
			default:
				cherchechaine(__FILE__, 40, buf, 0); /*"Nom de pays attendu "*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case CENT2:
			if (tok.id != FINLIGNE) {
				cherchechaine(__FILE__, 47, buf, 0); /*"Aller a la ligne apres le nom de pays"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			ungettoken(&tok);
			etat = CENT0;
			break;

		case CENT0:
			switch (tok.id) {
			case FINLIGNE:
				continue;
			case FINFICHIER:
				if (centrespays == 0) {
					cherchechaine(__FILE__, 41, buf, 1, pays->nom); /*"Pays %1 declare mais sans centre"*/
					avertir(buf);
				}
				(void) fclose(fd);
				verifcentres(ncentres);
				return;
			case CHAINE:
				if (cherchepays(tok.val) != NULL) {
					if (centrespays == 0) {
						cherchechaine(__FILE__, 42, buf, 1, pays->nom); /*"Pays %1 declare mais sans centre"*/
						avertir(buf);
					}
					ungettoken(&tok);
					etat = CENTINIT;
					continue;
				}

				if ((centre = cherchecentre(tok.val)) == NULL) {
					cherchechaine(__FILE__, 43, buf, 1, tok.val); /*"Centre %1 non declare sur une possession"*/
					erreurparse(NULL, LACARTE, FALSE, buf);
				}

				if (centrepossede(centre)) {
					cherchechaine(__FILE__, 44, buf, 1, tok.val); /*"Possession %1 apparaissant deux fois"*/
					erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
				}

				POSSESSION.t[POSSESSION.n].centre = centre;
				POSSESSION.t[POSSESSION.n].pays = pays;

				assert(++POSSESSION.n != NPOSSESSIONS);
				break;

			default:
				cherchechaine(__FILE__, 45, buf, 0); /*"Region du centre possede attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}

			etat = CENTFIN;
			break;

		case CENTFIN:
			if (tok.id != FINLIGNE && tok.id != FINFICHIER) {
				cherchechaine(__FILE__, 46, buf, 0); /*"Possession de centre trop longue, utiliser ';'"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			centrespays++;
			ncentres++;
			etat = CENT0;
			break;

		default:
			assert(FALSE); /* Devrait pas passer ici */
		}
	}
}

void parsesaisonparametre(char *nomsaison) {
	char buf[TAILLEMESSAGE];
	int n;

	n = atoi(nomsaison + 1);
	if (n < 1 || n > 99) {
		cherchechaine(__FILE__, 50, buf, 0); /*"Problème paramètre saison sur année"*/
		erreur(NULL, ERRPARAMS, buf);
	}

	switch (nomsaison[0]) {
	case 'P':
	case 'p':
		SAISON = n * 5;
		SAISONMODIF = (n - 1) * 5 + 3;
		break;
	case 'A':
	case 'a':
		SAISON = n * 5 + 2;
		SAISONMODIF = (n - 1) * 5 + 3;
		break;
	default:
		cherchechaine(__FILE__, 51, buf, 0); /*"Problème paramètre saison sur année saison"*/
		erreur(NULL, ERRPARAMS, buf);
	}
}
