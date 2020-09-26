#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"

/* Etats de l'automate lisant la commande */
typedef enum {
	PARAMINIT,
	PARAMORDRES,
	PARAMCARTE,
	PARAMSITINIT,
	PARAMXXX,
	PARAMPROTOS,
	PARAMPROTOS2,
	PARAMRECUP,
	PARAMRECUP2,
	PARAMSITFIN,
	PARAMARCHIVE,
	PARAMACTIFS,
	PARAMVIVANTS
} ETATAUTOPARAM;

/****************************************************************************************/
/* static char AUT[] = "Author : Jeremie Lefrancois"; */
/****************************************************************************************/
const char *nomvarenv = "DIPLOCOM";
const char *NOMPROGRAMME;
const char *LANGUE;

char *NOMSAISON[NSAISONS];
char *NOMSAISONAFFICHEE[NSAISONS];

char NOMFICCARTE[TAILLEMOT]; /* nom du sous repertoire carte */
char NOMFICORDRES[TAILLEMOT]; /* nom du fichier ordres */
char NOMFICSITUDEB[TAILLEMOT]; /* nom du fichier situation initiale */
char NOMFICSITUFIN[TAILLEMOT]; /* nom du fichier situation finale */
char NOMFICARCHIVE[TAILLEMOT]; /* nom du fichier archive */
char NOMFICACTIFS[TAILLEMOT]; /* nom du fichier pays actifs */
char NOMFICVIVANTS[TAILLEMOT]; /* nom du fichier pays vivants */
char NOMFICBILAN[TAILLEMOT]; /* nom du fichier bilan de la partie */
char NOMFICRECUP[TAILLEMOT]; /* nom du fichier dans lequel on recupere les ordres d'un pays */

char NOMFICPROTOS[NPAYSS][TAILLEMOT]; /* nom du fichier prototypes d'ordres */

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
TPOSSESSION POSSESSION, POSSESSIONAVANT;
TMOUVEMENT MOUVEMENT;
TRETRAITE RETRAITE;
TAJUSTEMENT AJUSTEMENT;
TINTERDIT INTERDIT;
TDELOGEE DELOGEE;
TANEANTIE ANEANTIE;
TDISPARITION DISPARITION;

TPAYSCLASSES PAYSCLASSES;

int ANNEEZERO, SAISON, SAISONMODIF;

BOOL OPTIONE, OPTIONw, OPTIONs, OPTIONv, OPTIONR, OPTIONS;
char OPTIONO, OPTIONC, OPTIONp[NPAYSS], OPTIONx[NPAYSS];

/****************************************************/

static void infos(void);
static void parametres(int argc, char **argv);
static void initialisation(void);

static void infos(void)
/* Affiche a l'ecran les options possibles, appelee par "diplo" sans parametres */
{
	char buf[TAILLEMESSAGE];

	cherchechaine(__FILE__, 1, buf, 0); /*"Options lors de l'appel du solveur DIPLO :"*/
	(void) printf("%s\n", buf);
	(void) printf("\n");

	cherchechaine(__FILE__, 71, buf, 0); /*"-fr 	: Utilise les messages en francais"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 72, buf, 0); /*"-en 	: Utilise les messages en anglais"*/
	(void) printf("%s\n", buf);
	(void) printf("\n");

	cherchechaine(__FILE__, 2, buf, 0); /*"-i <fic>	: Situation initiale lue dans <fic>)"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 3, buf, 0); /*"-o <fic>	: Ordres lus dans <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 4, buf, 0); /*"-f <fic>	: Situation finale dumpee dans <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 6, buf, 0); /*"-a <fic>	: Archivage des ordres dumpe dans <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 66, buf, 0); /*"-A <fic>	: Fournit les noms de pays actifs dans  <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 70, buf, 0); /*"-V <fic>	: Fournit les noms de pays vivants dans  <fic>"*/
	(void) printf("%s\n", buf);

	(void) printf("\n");

	cherchechaine(__FILE__, 9, buf, 0); /*"-c <rep>	: Sous repertoire ou trouver la carte <rep>"*/
	(void) printf("%s\n", buf);

	(void) printf("\n");

	cherchechaine(__FILE__, 10, buf, 0); /*"Pour ces commandes on adopte la convention suivante :"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 11, buf, 0); /*"			: Allemagne, Bangleterre, France, Hautriche, Italie, Russie, Turquie"*/
	(void) printf("%s\n", buf);

	(void) printf("\n");

	cherchechaine(__FILE__, 12, buf, 0); /*"-x<nm...>	: Fait les ordres des pays autres que  <n>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 13, buf, 0); /*"-O<n> <fic>	: Recupere les ordres du pays <n> dans <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 14, buf, 0); /*"-p<n> <fic>	: Cree des prototypes d'ordres du pays <n> dans <fic>"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 15, buf, 0); /*"-P<n> <fic>	: Cree des ordres du pays <n> dans <fic> (les plus simples)"*/
	(void) printf("%s\n", buf);

	(void) printf("\n");

	cherchechaine(__FILE__, 16, buf, 0); /*"-R			: Evite les destructions cas de defaut d'ordres de retraite"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 17, buf, 0); /*"-S			: La stabilite en centres entraine l'arret de la partie"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 18, buf, 0); /*"-E			: Calcule les eloignements (sortie standard)"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 19, buf, 0); /*"-C			: Verifie la carte"*/
	(void) printf("%s\n", buf);

	(void) printf("\n");

	cherchechaine(__FILE__, 20, buf, 0); /*"-w			: Branche le mode bavard"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 21, buf, 0); /*"-v			: Affiche la version du programme"*/
	(void) printf("%s\n", buf);
	cherchechaine(__FILE__, 65, buf, 0); /*"-s			: Branche le mode silencieux"*/
	(void) printf("%s\n", buf);

	(void) printf("\n");
}

static void parametres(int argc, char **argv)
/* Examine les parametres et met a jour les variables globales */
{
	int i, npays;
	ETATAUTOPARAM etat;
	BOOL ordresdejalus;
	char buf[TAILLEMESSAGE];

	ordresdejalus = FALSE;
	etat = PARAMINIT;
	npays = 0;

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
			} else if (!strcmp(*argv, "-o")) {
				if (etat != PARAMINIT)
					impromptu("'-o'");
				etat = PARAMORDRES;
			} else if (!strcmp(*argv, "-c")) {
				if (etat != PARAMINIT)
					impromptu("'-c'");
				etat = PARAMCARTE;
			} else if (!strcmp(*argv, "-f")) {
				if (etat != PARAMINIT)
					impromptu("'-f'");
				etat = PARAMSITFIN;
			} else if (!strcmp(*argv, "-a")) {
				if (etat != PARAMINIT)
					impromptu("'-a'");
				etat = PARAMARCHIVE;
			} else if (!strcmp(*argv, "-A")) {
				if (etat != PARAMINIT)
					impromptu("'-A'");
				etat = PARAMACTIFS;
			} else if (!strcmp(*argv, "-V")) {
				if (etat != PARAMINIT)
					impromptu("'-V'");
				etat = PARAMVIVANTS;
			} else if (!strcmp(*argv, "-w")) {
				if (etat != PARAMINIT)
					impromptu("'-w'");
				OPTIONw = TRUE;
			} else if (!strcmp(*argv, "-s")) {
				if (etat != PARAMINIT)
					impromptu("'-s'");
				OPTIONs = TRUE;
			} else if (!strcmp(*argv, "-R")) {
				if (etat != PARAMINIT)
					impromptu("'-R'");
				OPTIONR = TRUE;
			} else if (!strcmp(*argv, "-S")) {
				if (etat != PARAMINIT)
					impromptu("'-S'");
				OPTIONS = TRUE;
			} else if (!strcmp(*argv, "-C")) {
				if (etat != PARAMINIT)
					impromptu("'-C'");
				if (OPTIONE) {
					cherchechaine(__FILE__, 22, buf, 0); /*"Option -C et -E incompatibles"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				OPTIONC = TRUE;
			} else if (!strcmp(*argv, "-E")) {
				if (etat != PARAMINIT)
					impromptu("'-E'");
				if (OPTIONC) {
					cherchechaine(__FILE__, 23, buf, 0); /*"Option -E et -C incompatibles"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				OPTIONE = TRUE;
			} else if (!strcmp(*argv, "-v")) {
				if (etat != PARAMINIT)
					impromptu("'-v'");
				OPTIONv = TRUE;
				return; /* Ignore le reste */
			} else { /* options tracage */
				for (i = 1; (*argv)[i] != EOS; i++)
					switch ((*argv)[i]) {
					case 'x':
						if (etat != PARAMINIT) {
							cherchechaine(__FILE__, 24, buf, 0); /*"Option x"*/
							impromptu(buf);
						}
						etat = PARAMXXX;
						continue;
					case 'P':
					case 'p':
						if (etat != PARAMINIT) {
							cherchechaine(__FILE__, 25, buf, 0); /*"Option P/p"*/
							impromptu(buf);
						}
						etat = PARAMPROTOS;
						(void) strcat(OPTIONp, ((*argv)[i] == 'P' ? "A" : "a"));
						continue;
					case 'O':
						if (etat != PARAMINIT) {
							cherchechaine(__FILE__, 26, buf, 0); /*"Option O"*/
							impromptu(buf);
						}
						etat = PARAMRECUP;
						continue;
					default:
						switch (etat) {
						case PARAMXXX:
							sprintf(OPTIONx, "%c", (*argv)[i]);
							etat = PARAMINIT;
							break;
						case PARAMPROTOS:
							OPTIONp[npays] += ((*argv)[i] - 'A');
							etat = PARAMPROTOS2;
							break;
						case PARAMRECUP:
							OPTIONO = (*argv)[i];
							etat = PARAMRECUP2;
							break;
						default:
							cherchechaine(__FILE__, 29, buf, 0); /*"Initiale pays"*/
							impromptu(buf);
						}
						continue;
					}
				if (etat != PARAMPROTOS2 && etat != PARAMRECUP2)
					etat = PARAMINIT;
			}
		} else {
			if (strlen(*argv) > TAILLEMOT) {
				cherchechaine(__FILE__, 31, buf, 0); /*"Nom de fichier trop grand"*/
				erreur(NULL, ERRPARAMS, buf);
			}
			switch (etat) {
			case PARAMORDRES:
				if (ordresdejalus) {
					cherchechaine(__FILE__, 32, buf, 0); /*"Plus d'un fichier d'ordres"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				ordresdejalus = TRUE;
				(void) strcpy(NOMFICORDRES, *argv);
				etat = PARAMINIT;
				break;
			case PARAMCARTE:
				(void) strcpy(NOMFICCARTE, *argv);
				etat = PARAMINIT;
				break;
			case PARAMRECUP2:
				(void) strcpy(NOMFICRECUP, *argv);
				etat = PARAMINIT;
				break;
			case PARAMSITINIT:
				(void) strcpy(NOMFICSITUDEB, *argv);
				etat = PARAMINIT;
				break;
			case PARAMSITFIN:
				(void) strcpy(NOMFICSITUFIN, *argv);
				etat = PARAMINIT;
				break;
			case PARAMACTIFS:
				(void) strcpy(NOMFICACTIFS, *argv);
				etat = PARAMINIT;
				break;
			case PARAMVIVANTS:
				(void) strcpy(NOMFICVIVANTS, *argv);
				etat = PARAMINIT;
				break;
			case PARAMARCHIVE:
				(void) strcpy(NOMFICARCHIVE, *argv);
				etat = PARAMINIT;
				break;
			case PARAMPROTOS2:
				/* "@" est un synonyme de "" (bug DOS) */
				if (!strcmp(*argv, "@"))
					(void) strcpy(NOMFICPROTOS[npays], "");
				else
					(void) strcpy(NOMFICPROTOS[npays], *argv);
				if (++npays >= NPAYSS) {
					cherchechaine(__FILE__, 33, buf, 0); /*"Trop de pays pour les prototypes"*/
					erreur(NULL, ERRPARAMS, buf);
				}
				etat = PARAMINIT;
				break;
			default:
				cherchechaine(__FILE__, 34, buf, 0); /*"Nom de fichier"*/
				impromptu(buf);
			}
		}
	}

	if (etat != PARAMINIT) {
		cherchechaine(__FILE__, 35, buf, 0); /*"Fin ligne commmande"*/
		impromptu(buf);
	}

}

static void initialisation(void)
/* Initialise les variables globales */
{
	int npays;

	PAYS.n = 0;
	REGION.n = 0;
	CENTRE.n = 0;
	CENTREDEPART.n = 0;
	ZONE.n = 0;
	ARMEEVOISIN.n = 0;
	FLOTTEVOISIN.n = 0;
	UNITE.n = 0;
	POSSESSION.n = 0;
	POSSESSIONAVANT.n = 0;
	MOUVEMENT.n = 0;
	RETRAITE.n = 0;
	AJUSTEMENT.n = 0;
	INTERDIT.n = 0;
	DELOGEE.n = 0;
	ANEANTIE.n = 0;
	UNITEFUTURE.n = 0;
	DISPARITION.n = 0;

	OPTIONw = FALSE;
	OPTIONs = FALSE;
	OPTIONv = FALSE;
	OPTIONR = FALSE;
	OPTIONC = FALSE;
	OPTIONE = FALSE;

	OPTIONO = EOS;

	(void) strcpy(OPTIONx, "");
	(void) strcpy(OPTIONp, "");

	/* Valeurs par defaut */
	(void) strcpy(NOMFICCARTE, "DEFAULT");

	(void) strcpy(NOMFICSITUDEB, "");
	(void) strcpy(NOMFICORDRES, "");
	(void) strcpy(NOMFICSITUFIN, "");
	(void) strcpy(NOMFICARCHIVE, "");
	(void) strcpy(NOMFICACTIFS, "");
	(void) strcpy(NOMFICVIVANTS, "");
	(void) strcpy(NOMFICRECUP, "");
	(void) strcpy(NOMFICBILAN, "");

	for (npays = 0; npays < NPAYSS; npays++)
		(void) strcpy(NOMFICPROTOS[npays], "");

}

static void inverseparametrex(void)
{
	char buf[TAILLEMESSAGE];
	char buf2[TAILLEMOT];
	_PAYS *r, *pays;

	/* Now we invert Optionx logic */
	if(strcmp(OPTIONx, "")) {

		for (r = PAYS.t; r < PAYS.t + PAYS.n; r++)
			if (r->initiale == OPTIONx[0])
				break;

		if(r == PAYS.t + PAYS.n) {
			cherchechaine(__FILE__, 27, buf, 0); /*"Pas de pays de tel code initiale"*/
			erreur(NULL, ERRPARAMS, buf);
		}

		pays = r;

		strcpy(OPTIONx, "");
		for (r = PAYS.t; r < PAYS.t + PAYS.n; r++) 
			if(r != pays) {
				sprintf(buf2, "%c", r->initiale);
				strcat(OPTIONx, buf2);
			}
	}

}

int main(int argc, char *argv[]) {
	char *q, carte[TAILLENOMFIC];
	_PAYS *pays;
	int nbphases, npays;
	char buf[TAILLEMESSAGE], buf2[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	NOMPROGRAMME = "SOLVEUR";
	LANGUE = "fr"; /* par defaut */

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

		cherchechaine(__FILE__, 39, buf, 0); /*"Version basee sur DATC"*/
		(void) fprintf(stderr, "%s\n", buf);

		exit(0);
	}

	initialisetablevoisinages();

	addpath(carte, "DIPLO.DAT", TRUE);
	parsecarte(carte);
	if (OPTIONw) {
		cherchechaine(__FILE__, 41, buf, 0); /*"Fin lecture carte"*/
		informer(buf);
	}

	inverseparametrex();

	if (OPTIONE) {
		calculeeloignements();
		exit(0);
	}

	if (OPTIONC) {
		verifiecarte();
		exit(0);
	}

	parsesituation(NOMFICSITUDEB);
	if (OPTIONw) {
		cherchechaine(__FILE__, 44, buf, 0); /*"Fin lecture situation initiale"*/
		informer(buf);
	}

	if (strcmp(OPTIONp, "")) {
		for (npays = 0; OPTIONp[npays] != EOS; npays++) {
			if (islower((int) OPTIONp[npays])) {
				decritprototypes(NOMFICPROTOS[npays], 
				    paysdinitiale(toupper((int)OPTIONp[npays])));
			} else if (isupper((int) OPTIONp[npays])) {
				decritordressecurite(NOMFICPROTOS[npays], 
				    paysdinitiale(OPTIONp[npays]));
			} else {
				cherchechaine(__FILE__, 45, buf, 0); /*"Option Px ou px inconnue"*/
				erreur(NULL, ERRPARAMS, buf);
			}
		}
		exit(0);
	}

	nbphases = 0; /* Evite un avertissement du compilateur */

	switch ((IDSAISON) (SAISON % NSAISONS)) {

	case PRINTEMPS:
	case AUTOMNE: /* avant mouvements */
		if (OPTIONw) {
			cherchechaine(__FILE__, 46, buf, 0); /*"Il s'agit de resolution de mouvements"*/
			informer(buf);
		}
		if (strcmp(OPTIONx, "")) {
			(void) strcpy(buf2, "");
			for (q = OPTIONx; *q; q++) {
				pays = paysdinitiale(*q);
				creemouvements(pays);
				(void) strcat(buf2, pays->nom);
				(void) strcat(buf2, " ");
			}
		}
		parsemouvements(NOMFICORDRES);
		if (OPTIONw) {
			cherchechaine(__FILE__, 48, buf, 0); /*"Fin lecture mouvements"*/
			informer(buf);
		}
		verifmouvements();
		nbphases = resoudmouvements();
		modifmouvements();
		calculinterdites();
		calculaneanties();
		if((IDSAISON) (SAISON % NSAISONS) == AUTOMNE)
			suppressionelimines2();
		if (OPTIONw) {
			cherchechaine(__FILE__, 49, buf, 0); /*"Fin resolution mouvements"*/
			informer(buf);
		}
		break;

	case ETE: /* avant retraites */
		if (OPTIONw) {
			cherchechaine(__FILE__, 50, buf, 0); /*"Il s'agit de resolution de retraites"*/
			informer(buf);
		}
		if (strcmp(OPTIONx, "")) {
			(void) strcpy(buf2, "");
			for (q = OPTIONx; *q; q++) {
				pays = paysdinitiale(*q);
				creeretraites(pays);
				(void) strcat(buf2, pays->nom);
				(void) strcat(buf2, " ");
			}
		}
		parseretraites(NOMFICORDRES);
		if (OPTIONw) {
			cherchechaine(__FILE__, 52, buf, 0); /*"Fin lecture retraites ete"*/
			informer(buf);
		}
		verifretraites();
		nbphases = 1;
		modifretraites();
		finretraites();
		if (OPTIONw) {
			cherchechaine(__FILE__, 53, buf, 0); /*"Fin resolution retraites ete"*/
			informer(buf);
		}
		break;

	case HIVER: /* avant retraites + decompte */
		if (OPTIONw) {
			cherchechaine(__FILE__, 54, buf, 0); /*"Il s'agit de resolution de retraites (puis modif possessions)"*/
			informer(buf);
		}
		if (strcmp(OPTIONx, "")) {
			(void) strcpy(buf2, "");
			for (q = OPTIONx; *q; q++) {
				pays = paysdinitiale(*q);
				creeretraites(pays);
				(void) strcat(buf2, pays->nom);
				(void) strcat(buf2, " ");
			}
		}
		parseretraites(NOMFICORDRES);
		if (OPTIONw) {
			cherchechaine(__FILE__, 56, buf, 0); /*"Fin lecture retraites hiver"*/
			informer(buf);
		}
		verifretraites();
		nbphases = 1;
		modifretraites();
		if (OPTIONw) {
			cherchechaine(__FILE__, 57, buf, 0); /*"Fin resolution retraites hiver"*/
			informer(buf);
		}
		dupliquepossessions();
		modifpossessions();
		calculedisparitions();
		if (OPTIONw) {
			cherchechaine(__FILE__, 58, buf, 0); /*"Fin mise a jour possessions"*/
			informer(buf);
		}
		suppressionelimines();
		finretraites();
		if (OPTIONw) {
			cherchechaine(__FILE__, 69, buf, 0); /*"Fin suppression pays elimines"*/
			informer(buf);
		}
		break;

	case BILAN: /* avant ajustements */
		if (OPTIONw) {
			cherchechaine(__FILE__, 59, buf, 0); /*"Il s'agit de resolution d'ajustements"*/
			informer(buf);
		}
		if (strcmp(OPTIONx, "")) {
			(void) strcpy(buf2, "");
			for (q = OPTIONx; *q; q++) {
				pays = paysdinitiale(*q);
				creeajustements(pays);
				(void) strcat(buf2, pays->nom);
				(void) strcat(buf2, " ");
			}
		}
		parseajustements(NOMFICORDRES);
		if (OPTIONw) {
			cherchechaine(__FILE__, 61, buf, 0); /*"Fin lecture ajustements"*/
			informer(buf);
		}
		verifajustements();
		nbphases = 1;
		modifajustements();
		if (OPTIONw) {
			cherchechaine(__FILE__, 62, buf, 0); /*"Fin resolution ajustements"*/
			informer(buf);
		}
		break;
	}

	if (OPTIONO != EOS) {
		if (isupper((int) OPTIONO)) {
			decritordrescomplets(NOMFICRECUP, paysdinitiale(OPTIONO), TRUE);
			exit(0);
		} else {
			cherchechaine(__FILE__, 63, buf, 0); /*"Option Ox inconnue"*/
			erreur(NULL, ERRPARAMS, buf);
		}
	}

	if (strcmp(OPTIONx, "") && OPTIONw) {
		cherchechaine(__FILE__, 55, buf, 1, buf2); /*"Resolution partielle sans %1"*/
		informer(buf);
	}

	decritordres(NOMFICARCHIVE, TRUE);
	SAISON++;
	decritsituation(NOMFICSITUFIN);
	decritactifs(NOMFICACTIFS);
	decritvivants(NOMFICVIVANTS);

	(void) sprintf(bufn1, "%d", ANNEEZERO + (SAISON - 1) / NSAISONS);
	cherchechaine(__FILE__, 64, buf, 2, NOMSAISONAFFICHEE[(SAISON - 1)
			% NSAISONS], bufn1); /*"Resolution %1 %2"*/
	informer(buf);

	if (OPTIONw) {
		(void) sprintf(bufn1, "%d", nbphases);
		cherchechaine(__FILE__, 67, buf, 1, bufn1); /*"Resolution en %1 phase(s)"*/
		informer(buf);
	}

	exit(0);
	return 0; /* Trompe le compilateur */
}
