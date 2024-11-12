#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

#define NLECTURE 9
#define NPARSE 5
#define NVERIF 4
#define NERREUR 5

static char *LECTURE[NLECTURE];
static char *ERREURPARSE[NPARSE];
static char *ERREURVERIF[NVERIF];
static char *ERREUR[NERREUR];

/* Ces variables proviennent de parse.c */
extern int noligne;
extern int lecture;
extern char image[];

/********************************************************************/
/* exportee pour le module ploteur */

int vpays(_PAYS *pays) {
	_PAYS *p;
	int i;

	/* Etrange : avertissement sur le fait que 'i' pourrait etre utilise non initialise..
	 ... seulement quand on compile avec O3.. */

	for (p = PAYS.t, i = 0; p < PAYS.t + PAYS.n; p++, i++)
		if (p == pays)
			return i;

	assert(FALSE); /* On ne doit pas passer la */
	return 0; /* Trompe le compilateur */
}

/********************************************************************/
void initialisetablesaisons(void)
/* Pour le multilingue il a fallu calculer dynamiquement cette table */
{
	int i;
	char buf[TAILLEMESSAGE];

	/* table SAISON Utilisation */

	(void) sprintf(buf, "PRINTEMPS");
	NOMSAISON[PRINTEMPS] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISON[PRINTEMPS], buf);

	(void) sprintf(buf, "ETE");
	NOMSAISON[ETE] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISON[ETE], buf);

	(void) sprintf(buf, "AUTOMNE");
	NOMSAISON[AUTOMNE] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISON[AUTOMNE], buf);

	(void) sprintf(buf, "HIVER");
	NOMSAISON[HIVER] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISON[HIVER], buf);

	(void) sprintf(buf, "BILAN");
	NOMSAISON[BILAN] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISON[BILAN], buf);

	/* table SAISON Affichage */

	cherchechaine(__FILE__, 33, buf, 0); /*"Printemps"*/
	NOMSAISONAFFICHEE[PRINTEMPS] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISONAFFICHEE[PRINTEMPS], buf);

	cherchechaine(__FILE__, 35, buf, 0); /*"Ete"*/
	NOMSAISONAFFICHEE[ETE] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISONAFFICHEE[ETE], buf);

	cherchechaine(__FILE__, 37, buf, 0); /*"Automne"*/
	NOMSAISONAFFICHEE[AUTOMNE] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISONAFFICHEE[AUTOMNE], buf);

	cherchechaine(__FILE__, 39, buf, 0); /*"Hiver"*/
	NOMSAISONAFFICHEE[HIVER] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISONAFFICHEE[HIVER], buf);

	cherchechaine(__FILE__, 41, buf, 0); /*"Bilan"*/
	NOMSAISONAFFICHEE[BILAN] = malloc(strlen(buf) + 1);
	(void) strcpy(NOMSAISONAFFICHEE[BILAN], buf);

	/* Verification de coherence */
	for (i = 0; i < NSAISONS; i++) {
		assert(NOMSAISONAFFICHEE[i] != NULL);
		assert(NOMSAISON[i] != NULL);
	}

}

void initialisetableerreur(void)
/* Pour le multiliingue il a fallu calculer dynamiquement ces tables */
{
	int i;
	char buf[TAILLEMESSAGE];

	/* table LECTURE */
	cherchechaine(__FILE__, 2, buf, 0); /*"carte"*/
	LECTURE[CARTE] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[CARTE], buf);

	cherchechaine(__FILE__, 3, buf, 0); /*"annexe"*/
	LECTURE[ANNEXE] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[ANNEXE], buf);

	cherchechaine(__FILE__, 4, buf, 0); /*"situation"*/
	LECTURE[SITUATION] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[SITUATION], buf);

	cherchechaine(__FILE__, 5, buf, 0); /*"ordres"*/
	LECTURE[ORDRES] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[ORDRES], buf);

	cherchechaine(__FILE__, 45, buf, 0); /*"centres"*/
	LECTURE[CENTRES] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[CENTRES], buf);

	cherchechaine(__FILE__, 46, buf, 0); /*"unites"*/
	LECTURE[UNITES] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[UNITES], buf);

	cherchechaine(__FILE__, 47, buf, 0); /*"geographie"*/
	LECTURE[GEOGRAPHIE] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[GEOGRAPHIE], buf);

	cherchechaine(__FILE__, 48, buf, 0); /*"couleurs"*/
	LECTURE[COULEURS] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[COULEURS], buf);

	cherchechaine(__FILE__, 49, buf, 0); /*"codes"*/
	LECTURE[CODES] = malloc(strlen(buf) + 1);
	(void) strcpy(LECTURE[CODES], buf);

	/* Verification de coherence */
	for (i = 0; i < NLECTURE; i++)
		assert(LECTURE[i] != NULL);

	/* table ERREURPARSE */
	cherchechaine(__FILE__, 6, buf, 0); /*"probleme lexical"*/
	ERREURPARSE[LEXICALE] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURPARSE[LEXICALE], buf);

	cherchechaine(__FILE__, 7, buf, 0); /*"probleme syntaxique"*/
	ERREURPARSE[SYNTAXIQUE] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURPARSE[SYNTAXIQUE], buf);

	cherchechaine(__FILE__, 8, buf, 0); /*"mauvaise connaissance des regles"*/
	ERREURPARSE[LESREGLES] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURPARSE[LESREGLES], buf);

	cherchechaine(__FILE__, 9, buf, 0); /*"mauvaise connaissance de la carte"*/
	ERREURPARSE[LACARTE] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURPARSE[LACARTE], buf);

	cherchechaine(__FILE__, 10, buf, 0); /*"mauvaise connaissance de la situation"*/
	ERREURPARSE[LASITUATION] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURPARSE[LASITUATION], buf);

	/* Verification de coherence */
	for (i = 0; i < NPARSE; i++)
		assert(ERREURPARSE[i] != NULL);

	/* table ERREURVERIF */
	cherchechaine(__FILE__, 13, buf, 0); /*"ordre incoherent"*/
	ERREURVERIF[COHERENCE] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURVERIF[COHERENCE], buf);

	cherchechaine(__FILE__, 14, buf, 0); /*"ordre duplique"*/
	ERREURVERIF[DUPLIQUE] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURVERIF[DUPLIQUE], buf);

	cherchechaine(__FILE__, 15, buf, 0); /*"ordre manquant"*/
	ERREURVERIF[MANQUANT] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURVERIF[MANQUANT], buf);

	cherchechaine(__FILE__, 16, buf, 0); /*"entree incoherente"*/
	ERREURVERIF[ENTREE] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREURVERIF[ENTREE], buf);

	/* Verification de coherence */
	for (i = 0; i < NVERIF; i++)
		assert(ERREURVERIF[i] != NULL);

	/* table ERREUR */
	cherchechaine(__FILE__, 17, buf, 0); /*"parse d'un fichier"*/
	ERREUR[ERRPARSE] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREUR[ERRPARSE], buf);

	cherchechaine(__FILE__, 18, buf, 0); /*"verification non localisable"*/
	ERREUR[ERRVERIF] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREUR[ERRVERIF], buf);

	cherchechaine(__FILE__, 19, buf, 0); /*"verification localisable"*/
	ERREUR[ERRVERIF2] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREUR[ERRVERIF2], buf);

	cherchechaine(__FILE__, 21, buf, 0); /*"parametres de l'appel"*/
	ERREUR[ERRPARAMS] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREUR[ERRPARAMS], buf);

	cherchechaine(__FILE__, 22, buf, 0); /*"appel au systeme d'exploitation"*/
	ERREUR[ERRSYSTEME] = malloc(strlen(buf) + 1);
	(void) strcpy(ERREUR[ERRSYSTEME], buf);

	/* Verification de coherence */
	for (i = 0; i < NERREUR; i++)
		assert(ERREUR[i] != NULL);

}

/**********************************************************************/
/*              TOUS LES MESSAGES AFFICHABLES                         */
/**********************************************************************/

void erreurparse(_PAYS *pays, TYPEERREURPARSE typeerreurparse, BOOL finligne,
		const char *mess) {
	char buf[TAILLEMESSAGE], buf2[TAILLEMESSAGE];
	char buf3[3 * TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	if (!strcmp(image, ""))
		cherchechaine(__FILE__, 24, buf, 0); /*"(debut de la ligne)"*/
	else
		cherchechaine(__FILE__, 25, buf, 0); /*"<<<"*/
	(void) strcpy(buf2, buf);


	if (finligne) {
		(void) sprintf(bufn1, "%d", noligne - 1);
		cherchechaine(__FILE__, 26, buf, 1, bufn1); /*"a la fin de la ligne %1"*/
	} else {
		(void) sprintf(bufn1, "%d", noligne);
		cherchechaine(__FILE__, 27, buf, 1, bufn1); /*"en ligne %1"*/
	}

	if (OPTIONL) { /* do not mention lines */
		(void) sprintf(buf3, "%s%s\n%s : %s : %s : %s", image, buf2,
			LECTURE[lecture], ERREURPARSE[typeerreurparse],
			(pays == NULL ? "N/A" : pays->nom), mess);
	} else {
		(void) sprintf(buf3, "%s%s\n%s : %s : %s : %s %s", image, buf2,
			LECTURE[lecture], ERREURPARSE[typeerreurparse],
			(pays == NULL ? "N/A" : pays->nom), mess, buf);

	}

	erreur(pays, ERRPARSE, buf3);
}

void erreurverif(_PAYS *pays, TYPEERREURVERIF typeerreurverif, const char *mess) {
	char buf[TAILLEMESSAGE];
	char buf2[2 * TAILLEMESSAGE];

	cherchechaine(__FILE__, 28, buf, 0); /*"a la verification (pour les erreurs non localisables)"*/
	(void) sprintf(buf2, "%s : %s %s : %s", (pays == NULL ? "N/A" : pays->nom),
			ERREURVERIF[typeerreurverif], buf, mess);
	erreur(pays, ERRVERIF, buf2);
}

void erreurverif2(_PAYS *pays, TYPEERREURVERIF typeerreurverif, const char *mess) {
	char buf[TAILLEMESSAGE], buf2[TAILLEMESSAGE];
	char buf3[3 * TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	(void) sprintf(bufn1, "%d", noligne);
	cherchechaine(__FILE__, 27, buf, 1, bufn1); /*"en ligne %1"*/

	if (OPTIONL) { /* do not mention lines */
		cherchechaine(__FILE__, 29, buf2, 0); /*"a la verification (pour les erreurs localisables)"*/
		(void) sprintf(buf3, "%s : %s %s : %s", (pays == NULL ? "N/A"
			: pays->nom), ERREURVERIF[typeerreurverif], buf2, mess);
	} else {
		cherchechaine(__FILE__, 29, buf2, 0); /*"a la verification (pour les erreurs localisables)"*/
		(void) sprintf(buf3, "%s : %s %s : %s %s", (pays == NULL ? "N/A"
			: pays->nom), ERREURVERIF[typeerreurverif], buf2, mess, buf);
	}
	erreur(pays, ERRVERIF2, buf3);
}

void erreur(_PAYS *pays, TYPEERREUR typeerreur, const char *mess)
/* Toute erreur fatale qui va arreter le programme */
{
	char buf[TAILLEMESSAGE];
	char buf2[3 * TAILLEMESSAGE];

	cherchechaine(__FILE__, 30, buf, 0); /*"ERREUR"*/

	/* Erreur dans les parametres : les tables d'erreurs pas remplies encore */
	if (typeerreur == ERRPARAMS)
		(void) sprintf(buf2, "%s : %s :\n%s\n", NOMPROGRAMME, buf, mess);
	else
		(void) sprintf(buf2, "%s : %s %s :\n%s\n", NOMPROGRAMME, buf,
				ERREUR[typeerreur], mess);
	(void) fprintf(stderr, "%s", buf2);

	switch (typeerreur) {
	case ERRPARSE:
		exit(pays == NULL ? 220 : 221 + vpays(pays));
		break; /* Evite un message du lint */
	case ERRVERIF2:
		exit(pays == NULL ? 230 : 231 + vpays(pays));
		break; /* Evite un message du lint */
	case ERRVERIF:
		exit(pays == NULL ? 240 : 241 + vpays(pays));
		break; /* Evite un message du lint */
	case ERRPARAMS:
		exit(254);
		break; /* Evite un message du lint */
	case ERRSYSTEME:
		exit(255);
		break; /* Evite un message du lint */
	}
	assert(FALSE); /* Ne doit pas passer ici */
}

void informer(const char *mess) {
	char buf[TAILLEMESSAGE];
	char buf2[2 * TAILLEMESSAGE];

	cherchechaine(__FILE__, 31, buf, 0); /*"INFORMATION"*/
	(void) sprintf(buf2, "%s : %s : %s\n", NOMPROGRAMME, buf, mess);
	(void) fprintf(stderr, "%s", buf2);
}

void avertir(const char *mess) {
	char buf[TAILLEMESSAGE];
	char buf2[2 * TAILLEMESSAGE];

	cherchechaine(__FILE__, 32, buf, 0); /*"AVERTISSEMENT"*/
	(void) sprintf(buf2, "%s : %s : %s\n", NOMPROGRAMME, buf, mess);
	(void) fprintf(stderr, "%s", buf2);
}

	char buf[TAILLEMESSAGE];
	char buf2[2 * TAILLEMESSAGE];

void impromptu(const char *mess) {
	cherchechaine(__FILE__, 44, buf, 1, mess); /*"Inattendu"*/
	(void) sprintf(buf2, "%s %s", buf, mess);
	erreur(NULL, ERRPARAMS, buf);
}
