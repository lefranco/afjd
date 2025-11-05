#include "../solveur/define.h"
#include "define2.h"
#include "../solveur/struct.h"
#include "../solveur/includes.h"
#include "../solveur/protos.h"
#include "protos2.h"
#include "../solveur/datas.h"

#define NSAISONS 5

/* Etats de l'automate lisant la commande */
typedef enum {
	PARAMINIT,
	PARAMORDRES,
	PARAMCENTRES,
	PARAMUNITES,
	PARAMCARTE,
	PARAMSITINIT,
	PARAMSAISON
} ETATAUTOPARAM;

/********************************************************/
/* static char AUT[] = "Author : Jeremie Lefrancois"; */
/********************************************************/
const char *nomvarenv = "DIPLOCOM";

const char *NOMPROGRAMME;
const char *LANGUE;

char *NOMSAISON[NSAISONS];
char *NOMSAISONAFFICHEE[NSAISONS];

char NOMFICORDRES[TAILLEMOT]; /* nom du fichier ordres */
char NOMFICCENTRES[TAILLEMOT]; /* nom du fichier centres */
char NOMFICUNITES[TAILLEMOT]; /* nom du fichier unites */
char NOMFICCARTE[TAILLEMOT]; /* nom du fichier carte */
char NOMFICSITU[TAILLEMOT]; /* nom du fichier situation */

TPAYS PAYS;
TREGION REGION;
TCENTRE CENTRE;
TCENTREDEPART CENTREDEPART;
TZONE ZONE;
TARMEEVOISIN ARMEEVOISIN;
TFLOTTEVOISIN FLOTTEVOISIN;
TELOIGNEMENT ELOIGNEMENT;
TUNITE UNITE;
TUNITEFUTURE UNITEFUTURE;
TPOSSESSION POSSESSION;
TPOSSESSION POSSESSIONAVANT;
TMOUVEMENT MOUVEMENT;
TRETRAITE RETRAITE;
TAJUSTEMENT AJUSTEMENT;
TINTERDIT INTERDIT;
TDELOGEE DELOGEE;
TANEANTIE ANEANTIE;
TDISPARITION DISPARITION;

TPAYSCLASSES PAYSCLASSES;

int ANNEEZERO, SAISON, SAISONMODIF;
BOOL OPTIONw, OPTIONl, OPTIONs, OPTIONv, OPTIONo, OPTIONC, OPTIONU;
/****************************************************/

static void infos(void);
static void parametres(int argc, char **argv);
static void initialisation(void);

static void infos(void)
/* Affiche a l'ecran les options possibles, appelee par "diplo" sans parametres */
{
	char buf[TAILLEMESSAGE];

	cherchechaine(__FILE__, 1, buf, 0); /*"Option lors de l'appel de l'aideur DIPLO :"*/
	(void) printf("\n");

	cherchechaine(__FILE__, 25, buf, 0); /*"-fr 	: Utilise les messages en francais"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 26, buf, 0); /*"-en 	: Utilise les messages en anglais"*/
	(void) printf("%s\n", buf);
	(void) printf("\n");

	cherchechaine(__FILE__, 2, buf, 0); /*"-i <fic>        : Situation initiale inscrite dans <fic> (def : SITU1.DAT)"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 3, buf, 0); /*"-o <fic>        : Ordres lus dans <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 4, buf, 0); /*"-C <fic>        : Centres possedes lus dans <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 5, buf, 0); /*"-U <fic>        : Unités lues dans <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 24, buf, 0); /*"-S <saison>    : Saison indiquée sous la forme P07"*/
	(void) printf("%s\n", buf);

	(void) printf("\n");

	cherchechaine(__FILE__, 6, buf, 0); /*"-w              : Branche le mode bavard"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 7, buf, 0); /*"-c <rep>        : Sous repertoire ou trouver la carte"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 8, buf, 0); /*"-v              : Affiche la version du programme"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 9, buf, 0); /*"-s              : Branche le mode silencieux"*/
	(void) printf("%s\n", buf);

	(void) printf("\n");
}

static void parametres(int argc, char **argv)
/* Examine les parametres et met a jour les variables globales */
{
	ETATAUTOPARAM etat;
	BOOL ordresdejalus;
	BOOL centresdejalus;
	BOOL unitesdejalues;
	char buf[TAILLEMESSAGE];

	ordresdejalus = FALSE;
	centresdejalus = FALSE;
	unitesdejalues = FALSE;
	etat = PARAMINIT;

	while (--argc > 0) {
		++argv;
		if ((*argv)[0] == '-') {
			if (!strcmp(*argv, "-fr")) {
				if (etat != PARAMINIT)
					impromptu("'-fr'");
				LANGUE = "fr";
			} else if (!strcmp(*argv, "-en")) {
				if (etat != PARAMINIT)
					impromptu("'-en'");
				LANGUE = "en";
			} else if (!strcmp(*argv, "-i")) {
				if (etat != PARAMINIT)
					impromptu("'-i'");
				etat = PARAMSITINIT;
			} else if (!strcmp(*argv, "-c")) {
				if (etat != PARAMINIT)
					impromptu("'-c'");
				etat = PARAMCARTE;
			} else if (!strcmp(*argv, "-o")) {
				if (etat != PARAMINIT)
					impromptu("'-o'");
				OPTIONo = TRUE;
				etat = PARAMORDRES;
			} else if (!strcmp(*argv, "-C")) {
				if (etat != PARAMINIT)
					impromptu("'-C'");
				OPTIONC = TRUE;
				etat = PARAMCENTRES;
			} else if (!strcmp(*argv, "-U")) {
				if (etat != PARAMINIT)
					impromptu("'-U'");
				OPTIONU = TRUE;
				etat = PARAMUNITES;
			} else if (!strcmp(*argv, "-w")) {
				if (etat != PARAMINIT)
					impromptu("Option w");
				OPTIONw = TRUE;
			} else if (!strcmp(*argv, "-s")) {
				if (etat != PARAMINIT)
					impromptu("Option s");
				OPTIONs = TRUE;
			} else if (!strcmp(*argv, "-S")) {
				if (etat != PARAMINIT)
					impromptu("Option S");
				etat = PARAMSAISON;
			} else if (!strcmp(*argv, "-v")) {
				if (etat != PARAMINIT)
					impromptu("Option v");
				OPTIONv = TRUE;
				return; /* Ignore le reste */
			} else { /* options tracage */
				cherchechaine(__FILE__, 10, buf, 0); /*"Pays ou option fantaisiste"*/
				erreur(NULL, ERRPARAMS, buf);
			}
		} else {
			if (strlen(*argv) > TAILLEMOT) {
				cherchechaine(__FILE__, 11, buf, 0); /*"Nom de fichier trop grand"*/
				erreur(NULL, ERRPARAMS, buf);
			}
			switch (etat) {
			case PARAMORDRES:
				if (unitesdejalues) {
					cherchechaine(__FILE__, 12, buf, 0); /*"Unites et ordres incompatibles"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				if (ordresdejalus) {
					cherchechaine(__FILE__, 13, buf, 0); /*"Plus d'un fichiers d'ordres a lire"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				(void) strcpy(NOMFICORDRES, *argv);
				ordresdejalus = TRUE;
				etat = PARAMINIT;
				break;
			case PARAMCENTRES:
				if (centresdejalus) {
					cherchechaine(__FILE__, 14, buf, 0); /*"Plus d'un fichiers de posessions a lire"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				(void) strcpy(NOMFICCENTRES, *argv);
				centresdejalus = TRUE;
				etat = PARAMINIT;
				break;
			case PARAMUNITES:
				if (ordresdejalus) {
					cherchechaine(__FILE__, 15, buf, 0); /*"Unites et ordres incompatibles"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				if (unitesdejalues) {
					cherchechaine(__FILE__, 16, buf, 0); /*"Plus d'un fichiers d'unites a lire"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				(void) strcpy(NOMFICUNITES, *argv);
				unitesdejalues = TRUE;
				etat = PARAMINIT;
				break;
			case PARAMCARTE:
				(void) strcpy(NOMFICCARTE, *argv);
				etat = PARAMINIT;
				break;
			case PARAMSAISON:
				parsesaisonparametre(*argv);
				etat = PARAMINIT;
				break;
			case PARAMSITINIT:
				(void) strcpy(NOMFICSITU, *argv);
				etat = PARAMINIT;
				break;
			default:
				cherchechaine(__FILE__, 17, buf, 0); /*"Nom de fichier"*/
				impromptu(buf);
			}
		}
	}

	if (etat != PARAMINIT) {
		cherchechaine(__FILE__, 18, buf, 0); /*"Fin de ligne de commande"*/
		impromptu(buf);
	}

}

static void initialisation(void)
/* Initialise les variables globales */
{

	PAYS.n = 0;
	REGION.n = 0;
	CENTRE.n = 0;
	CENTREDEPART.n = 0;
	ZONE.n = 0;
	ARMEEVOISIN.n = 0;
	FLOTTEVOISIN.n = 0;
	UNITE.n = 0;
	POSSESSION.n = 0;
	MOUVEMENT.n = 0;
	RETRAITE.n = 0;
	AJUSTEMENT.n = 0;
	INTERDIT.n = 0;
	DELOGEE.n = 0;
	UNITEFUTURE.n = 0;
	DISPARITION.n = 0;

	OPTIONw = FALSE;
	OPTIONl = FALSE;
	OPTIONs = FALSE;
	OPTIONv = FALSE;

	/* Valeurs par defaut */
	(void) strcpy(NOMFICCARTE, "HASBRO");

	(void) strcpy(NOMFICSITU, "");
	(void) strcpy(NOMFICORDRES, "");

	SAISON = 1;
	SAISONMODIF = 1;
}

int main(int argc, char *argv[]) {
	char carte[TAILLENOMFIC];
	char buf[TAILLEMESSAGE];

	NOMPROGRAMME = "AIDEUR";
	LANGUE = "en"; /* par defaut */

	initialisation();
	parametres(argc, argv);
	initialisetableerreur();
	initialisetablesaisons();

	/* Pour la gloire */
	/* if(!OPTIONs)
	 (void) fprintf(stderr,"%s\n",AUT); */

	if (argc == 1) {
		infos();
		exit(0);
	}

	if (OPTIONv) {
		cherchechaine(__FILE__, 19, buf, 0); /*"Pour aide : synthese situation a partir des mouvements"*/
		(void) fprintf(stderr, "%s\n", buf);
		exit(0);
	}

	addpath(carte, "DIPLO.DAT", TRUE);
	parsecarte(carte);
	if (OPTIONw) {
		cherchechaine(__FILE__, 20, buf, 0); /*"Fin lecture carte"*/
		informer(buf);
	}


	if (OPTIONo)
		parsemouvements2(NOMFICORDRES);

	if (OPTIONU)
		parseunites2(NOMFICUNITES);

	if (OPTIONC)
		parsecentres2(NOMFICCENTRES);

	switch ((IDSAISON) (SAISON % 5)) {
	case PRINTEMPS:
	case AUTOMNE:
		verifglobale((IDSAISON) (SAISON % 5));
		break;
	default:
		break;
	}

	if (OPTIONw) {
		cherchechaine(__FILE__, 22, buf, 0); /*"Fin lecture ordres"*/
		informer(buf);
	}

	decritsituation(NOMFICSITU);

	if (OPTIONw) {
		cherchechaine(__FILE__, 23, buf, 0); /*"Fin synthese situation"*/
		informer(buf);
	}

	exit(0);
	return 0; /* Trompe le compilateur */
}
