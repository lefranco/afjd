#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

#include "parse.h"


TCOTEPOSSS COTEPOSS;

/* Pour accelerer la recherche des voisinages, on stoque dans une table */
extern BOOL TABLEVOISINAGEFLOTTE[NZONES][NZONES];
extern BOOL TABLEVOISINAGEARMEE[NZONES][NZONES];

/* Ces infos seront remplie dans parse.c et exploitees dans la procedure erreurparse() de erreur.c si elle est appellee */
char image[TAILLEMESSAGE];
int lecture;
int noligne;

static LOOKAHEAD lookahead;
static BOOL changeligne;

static void inserecotepossible(char *);

static void parsepays(FILE *);
static void parseregion(FILE *);
static void parsecentre(FILE *);
static void parsecentredepart(FILE *);
static void parsezone(FILE *);
static void parsearmeevoisin(FILE *);
static void parseflottevoisin(FILE *);
static void parseunite(FILE *);
static void parsepossession(FILE *);
static void parseinterdit(FILE *);
static void parsedelogee(FILE *);
static void parseanneezero(FILE *);
static void parsesaison(FILE *);
static void parseeloignement(FILE *);
static void parsesaisonmodif(FILE *);

static void verifdisparitions(void);

/*********************************************************************************/
/*                          ROUTINES DU PARSEUR                                  */
/*********************************************************************************/
/* Visibles depuis le module ploteur */

void readtoken(char *word, TOKEN *tok) {
	char buf[TAILLEMESSAGE];
	char buf1[20];
	char buf2[20];

	switch (CODE(word[0],word[1])) {

	case CODE('P','A'):
		if (!strcmp(word, "PAYS")) {
			tok->id = UNPAYS;
			return;
		}
		break;
	case CODE('B','O'):
		if (!strcmp(word, "BOURREAU")) {
			tok->id = UNBOURREAU;
			return;
		}
		break;
	case CODE('R','E'):
		if (!strcmp(word, "REGION")) {
			tok->id = UNEREGION;
			return;
		}
		if (!strcmp(word, "REMOVE")) {
			cherchechaine(__FILE__, 236, buf, 0); /*"Il est preferable d'utiliser '-' plutot que 'REMOVE' pour retirer une unite"*/
			informer(buf);
			tok->id = UNREMOVE;
			return;
		}
		break;
	case CODE('Z','O'):
		if (!strcmp(word, "ZONE")) {
			tok->id = UNEZONE;
			return;
		}
		break;
	case CODE('M','E'):
		if (!strcmp(word, "MER")) {
			tok->id = UNEMER;
			return;
		}
		break;
	case CODE('T','E'):
		if (!strcmp(word, "TERRE")) {
			tok->id = UNETERRE;
			return;
		}
		break;
	case CODE('F','L'):
		if (!strcmp(word, "FLOTTEVOISIN")) {
			tok->id = UNFLOTTEVOISIN;
			return;
		}
		break;
	case CODE('A','R'):
		if (!strcmp(word, "ARMEEVOISIN")) {
			tok->id = UNARMEEVOISIN;
			return;
		}
		break;
	case CODE('A',EOS):
		if (!strcmp(word, "A")) {
			tok->id = UNEARMEESUICIDE;
			return;
		}
		break;
	case CODE('F',EOS):
		if (!strcmp(word, "F")) {
			tok->id = UNEFLOTTE;
			return;
		}
		break;
	case CODE('U','N'):
		if (!strcmp(word, "UNITE")) {
			tok->id = UNEUNITE;
			return;
		}
		break;
	case CODE('P','O'):
		if (!strcmp(word, "POSSESSION")) {
			tok->id = UNEPOSSESSION;
			return;
		}
		break;
	case CODE('I','N'):
		if (!strcmp(word, "INTERDIT")) {
			tok->id = UNINTERDIT;
			return;
		}
		break;
	case CODE('D','E'):
		if (!strcmp(word, "DELOGEE")) {
			tok->id = UNEDELOGEE;
			return;
		}
		break;
	case CODE('O','R'):
		if (!strcmp(word, "ORIGINE")) {
			tok->id = UNEORIGINE;
			return;
		}
		break;
	case CODE('D','I'):
		if (!strcmp(word, "DISPARITION")) {
			tok->id = UNEDISPARITION;
			return;
		}
		break;
	case CODE('-',EOS):
		if (!strcmp(word, "-")) {
			tok->id = UNEATTAQUESUPPRESSION;
			return;
		}
		break;
	case CODE('T','O'):
		if (!strcmp(word, "TO")) {
			cherchechaine(__FILE__, 1, buf, 0); /*"Utiliser '-' plutot que 'TO'"*/
			avertir(buf);
			tok->id = UNEATTAQUESUPPRESSION;
			return;
		}
		break;
	case CODE('S',EOS):
		if (!strcmp(word, "S")) {
			tok->id = UNSOUTIEN;
			return;
		}
		break;
	case CODE('C',EOS):
		if (!strcmp(word, "C")) {
			tok->id = UNCONVOI;
			return;
		}
		break;
	case CODE('H',EOS):
	case CODE('T',EOS):
	case CODE('H','O'):
	case CODE('X','X'):
		if (!strcmp(word, "H")) {
			tok->id = UNSTAND;
			return;
		}
		if (!strcmp(word, "T")) {
			cherchechaine(__FILE__, 2, buf, 0); /*"Utiliser 'H' plutot que 'T'"*/
			avertir(buf);
			tok->id = UNSTAND;
			return;
		}
		if (!strcmp(word, "HOLD") || !strcmp(word, "HOLDS")) {
			cherchechaine(__FILE__, 31, buf, 0); /*"Utiliser 'H' plutot que 'HOLD' ou 'HOLDS' "*/
			informer(buf);
			tok->id = UNSTAND;
			return;
		}
		if (!strcmp(word, "XXX")) {
			cherchechaine(__FILE__, 249, buf, 0); /*"Utiliser 'H' plutot que 'XXX' "*/
			informer(buf);
			tok->id = UNSTAND;
			return;
		}
		break;
	case CODE('R',EOS):
		if (!strcmp(word, "R")) {
			tok->id = UNERETRAITE;
			return;
		}
		break;
	case CODE('D',EOS):
		if (!strcmp(word, "D")) {
			tok->id = UNSUICIDE;
			return;
		}
		break;
	case CODE('O','T'):
		if (!strcmp(word, "OTB")) {
			tok->id = UNOFFTHEBOARD;
			return;
		}
		break;
	case CODE('+',EOS):
	case CODE('B',EOS):
	case CODE('B','U'):
		if (!strcmp(word, "B")) {
			cherchechaine(__FILE__, 230, buf, 0); /*"Il est preferable d'utiliser '+' plutot que 'B' pour construire une unite"*/
			informer(buf);
			tok->id = UNAJOUT; /* Tolerance ! */
			return;
		}
		if (!strcmp(word, "BUILD")) {
			cherchechaine(__FILE__, 235, buf, 0); /*"Il est preferable d'utiliser '+' plutot que 'BUILD' pour construire une unite"*/
			informer(buf);
			tok->id = UNAJOUT; /* Tolerance ! */
			return;
		}
		if (!strcmp(word, "+")) {
			tok->id = UNAJOUT;
			return;
		}
		break;
	case CODE('(',EOS):
		if (!strcmp(word, "(")) {
			tok->id = UNEOUVRANTE;
			return;
		}
		break;
	case CODE(')',EOS):
		if (!strcmp(word, ")")) {
			tok->id = UNEFERMANTE;
			return;
		}
		break;
	case CODE('/',EOS):
		if (!strcmp(word, "/")) {
			tok->id = UNSLASH;
			return;
		}
		break;
	case CODE('A','N'):
		if (!strcmp(word, "ANNEEZERO")) {
			tok->id = UNEANNEEZERO;
			return;
		}
		break;
	case CODE('S','A'):
		if (!strcmp(word, "SAISON")) {
			tok->id = UNESAISON;
			return;
		}
		if (!strcmp(word, "SAISONMODIF")) {
			tok->id = UNESAISONMODIF;
			return;
		}
		break;
	case CODE('M','I'):
		if (!strcmp(word, "MINUSCULES")) {
			tok->id = UNEMINUSCULES;
			return;
		}
		break;
	case CODE('M','A'):
		if (!strcmp(word, "MAJUSCULES")) {
			tok->id = UNEMAJUSCULES;
			return;
		}
		break;
	case CODE('P','R'):
		if (!strcmp(word, "PRINTEMPS")) {
			tok->id = UNPRINTEMPS;
			return;
		}
		break;
	case CODE('E','T'):
		if (!strcmp(word, "ETE")) {
			tok->id = UNETE;
			return;
		}
		break;
	case CODE('A','U'):
		if (!strcmp(word, "AUTOMNE")) {
			tok->id = UNAUTOMNE;
			return;
		}
		break;
	case CODE('H','I'):
		if (!strcmp(word, "HIVER")) {
			tok->id = UNHIVER;
			return;
		}
		break;
	case CODE('B','I'):
		if (!strcmp(word, "BILAN")) {
			tok->id = UNBILAN;
			return;
		}
		break;
	case CODE('E','L'):
		if (!strcmp(word, "ELOIGNEMENT")) {
			tok->id = UNELOIGNEMENT;
			return;
		}
		break;
	case CODE('C','N'):
	case CODE('N','C'):
		if (!strcmp(word, "CN")) {
			tok->id = UNECOTENORD;
			(void) strcpy(tok->val, "CN");
			return;
		}
		if (!strcmp(word, "NC")) {
			tok->id = UNECOTENORD;
			(void) strcpy(tok->val, "NC");
			return;
		}
		break;
	case CODE('C','S'):
	case CODE('S','C'):
		if (!strcmp(word, "CS")) {
			tok->id = UNECOTESUD;
			(void) strcpy(tok->val, "CS");
			return;
		}
		if (!strcmp(word, "SC")) {
			tok->id = UNECOTESUD;
			(void) strcpy(tok->val, "SC");
			return;
		}
		break;
	case CODE('C','E'):
	case CODE('E','C'):
		if (!strcmp(word, "CENTRE")) {
			tok->id = UNCENTRE;
			return;
		}
		if (!strcmp(word, "CENTREDEPART")) {
			tok->id = UNCENTREDEPART;
			return;
		}
		if (!strcmp(word, "CE")) {
			tok->id = UNECOTEEST;
			(void) strcpy(tok->val, "CE");
			return;
		}
		if (!strcmp(word, "EC")) {
			tok->id = UNECOTEEST;
			(void) strcpy(tok->val, "EC");
			return;
		}
		break;
	case CODE('C','O'):
	case CODE('W','C'):
		if (!strcmp(word, "COULEUR")) {
			tok->id = UNECOULEUR;
			return;
		}
		if (!strcmp(word, "CODE")) {
			tok->id = UNCODE;
			return;
		}
		if (!strcmp(word, "COTE")) {
			tok->id = UNECOTE;
			return;
		}
		if (!strcmp(word, "CO")) {
			tok->id = UNECOTEOUEST;
			(void) strcpy(tok->val, "CO");
			return;
		}
		if (!strcmp(word, "WC")) {
			tok->id = UNECOTEOUEST;
			(void) strcpy(tok->val, "WC");
			return;
		}
		if (!strcmp(word, "CONVOY")) {
			tok->id = UNCONVOY;
			return;
		}
		break;
	case CODE('V','I'):
		if (!strcmp(word, "VIA")) {
			tok->id = UNVIA;
			return;
		}
		break;
	}

	if (isdigit((int) word[0])) {
		tok->id = NOMBRE;
		tok->val2 = atoi(word);
		return;
	}
	if (isalpha((int) word[0])) {
		tok->id = CHAINE;
		(void) strcpy(tok->val, word);
	} else {
		if('%' == word[0]) {
			(void) sprintf(buf1, "%c%c", word[0],word[0]);
			(void) sprintf(buf2, "ASCII %xH", word[0]);
		} else {
			(void) sprintf(buf1, "%c", word[0]);
			(void) sprintf(buf2, "ASCII %xH", word[0]);
		}
		cherchechaine(__FILE__, 5, buf, 2, buf1, buf2); /*"Caractere non reconnu par l'analyseur lexical"*/
		erreurparse(NULL, LEXICALE, FALSE, buf);
	}

}

void ungettoken(TOKEN *tok) {
	TOKEN *p;

	if (tok->id == FINLIGNE)
		noligne--;

	p = lookahead.t + lookahead.n++;
	p->id = tok->id;
	(void) strcpy(p->val, tok->val);
	p->val2 = tok->val2;
}

void gettoken(FILE *fd, TOKEN *tok) {
	int c;
	char buf[TAILLEMOT];
	char *ps, *pssup;
	TOKEN *p;

	if (lookahead.n) {
		p = lookahead.t + --lookahead.n;
		if (p->id == FINLIGNE)
			noligne++;
		tok->id = p->id;
		(void) strcpy(tok->val, p->val);
		tok->val2 = p->val2;
		return;
	}

	for (;;) {
		while ((c = getc(fd)), c == ' ' || c == '\t')
			;
		switch (c) {
		case EOF:
			tok->id = FINFICHIER;
			if (lecture == ORDRES)
				changeligne = TRUE;
			return;
		case 13: /* Pour unix */
			continue;
		case '\n':
			tok->id = FINLIGNE;
			if (++noligne > NLIGNES && lecture == ORDRES) {
				cherchechaine(__FILE__, 6, buf, 0); /*"Trop de lignes"*/
				erreurparse(NULL, LEXICALE, FALSE, buf);
			}
			if (lecture == ORDRES)
				changeligne = TRUE;
			return;
		case ';':
			while ((c = getc(fd)), c != '\n' && c != EOF)
				;
			(void) ungetc(c, fd);
			continue;
		default:
			ps = buf;
			pssup = buf + TAILLEMOT;
			c = toupper(c);
			if (!(isalpha(c) || isdigit(c))) {
				*ps++ = (char) c;
			} else
				for (;;) {
					if (!(isalpha(c) || isdigit(c))) {
						(void) ungetc(c, fd);
						break;
					}
					*ps++ = (char) c;
					if (ps == pssup) {
						cherchechaine(__FILE__, 7, buf, 0); /*"Token trop long"*/
						erreurparse(NULL, LEXICALE, FALSE, buf);
					}
					c = getc(fd);
					c = toupper(c);
				}
			*ps = EOS;
			readtoken(buf, tok);
			if (lecture == ORDRES) {
				if (changeligne) {
					(void) strcpy(image, "");
					changeligne = FALSE;
				}
				(void) strcat(image, buf);
				(void) strcat(image, " ");
			}
			return;
		}
	}
}

/*********************************************************************************/
/*                              LA CARTE                                       */
/*********************************************************************************/

static void inserecotepossible(char *nom) {
	_COTEPOSS *p;

	for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++)
		if (!strcmp(p->nom, nom))
			return;

	(void) strcpy(COTEPOSS.t[COTEPOSS.n++].nom, nom);
	assert(COTEPOSS.n <= NCOTESPOSSS);

}

static void parsepays(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 8, buf, 0); /*"Definition d'un pays"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	(void) strcpy(PAYS.t[PAYS.n].nom, tok.val);

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 225, buf, 0); /*"Initiale d'un pays"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}
	if (strlen(tok.val) != 2) {
		cherchechaine(__FILE__, 226, buf, 0); /*"Taille de l'initiale d'un pays"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}
	PAYS.t[PAYS.n].initiale = tok.val[1];

	gettoken(fd, &tok);
	switch (tok.id) {
	case CHAINE:
		(void) strcpy(PAYS.t[PAYS.n].adjectif, tok.val);
		gettoken(fd, &tok);
		if (tok.id != FINLIGNE) {
			cherchechaine(__FILE__, 9, buf, 0); /*"Manque fin de ligne apres pays"*/
			erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
		}
		break;
	default:
		cherchechaine(__FILE__, 10, buf, 0); /*"Manque adjectif ou fin de ligne apres pays"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++PAYS.n != NPAYSS);
}

static void parseregion(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 12, buf, 0); /*"Probleme definition d'une region"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	(void) strcpy(REGION.t[REGION.n].nom, tok.val);

	gettoken(fd, &tok);
	switch (tok.id) {
	case CHAINE:
		(void) strcpy(REGION.t[REGION.n].nom2, tok.val);
		gettoken(fd, &tok);
		if (tok.id != FINLIGNE) {
			cherchechaine(__FILE__, 13, buf, 0); /*"Manque fin de ligne apres region"*/
			erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
		}
		break;
	case FINLIGNE:
		(void) strcpy(REGION.t[REGION.n].nom2, "");
		break;
	default:
		cherchechaine(__FILE__, 14, buf, 0); /*"Manque deuxieme nom ou fin de ligne apres region"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++REGION.n != NREGIONS);
}

static void parsecentre(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 16, buf, 0); /*"Probleme definition d'un centre sur la region"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((CENTRE.t[CENTRE.n].region = chercheregion(tok.val)) == NULL) {
		cherchechaine(__FILE__, 17, buf, 1, tok.val); /*"Region %1 non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 18, buf, 0); /*"Manque fin de ligne apres centre"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++CENTRE.n != NCENTRES);

}

static void parsecentredepart(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 20, buf, 0); /*"Probleme definition d'un centredepart sur le pays"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((CENTREDEPART.t[CENTREDEPART.n].pays = cherchepays(tok.val)) == NULL) {
		cherchechaine(__FILE__, 21, buf, 1, tok.val); /*"Pays %1 non declare pour un centredepart"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 22, buf, 0); /*"Probleme definition d'un centredepart sur le centre"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((CENTREDEPART.t[CENTREDEPART.n].centre = cherchecentre(tok.val))
			== NULL) {
		cherchechaine(__FILE__, 23, buf, 1, tok.val); /*"Centre %1 non declare sur un centredepart"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 24, buf, 0); /*"Manque fin de ligne apres centredepart"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++CENTREDEPART.n != NCENTREDEPARTS);
}

static void parsezone(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];
	static int rangzone = 0; /* Pour optimiser les calculs de voisinage, on memorise les rangs des zones */

	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTE:
		ZONE.t[ZONE.n].typezone = COTE;
		break;
	case UNEMER:
		ZONE.t[ZONE.n].typezone = MER;
		break;
	case UNETERRE:
		ZONE.t[ZONE.n].typezone = TERRE;
		break;
	default:
		cherchechaine(__FILE__, 26, buf, 0); /*"Probleme definition d'une zone sur le type"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 27, buf, 0); /*"Probleme definition d'une zone sur la region"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((ZONE.t[ZONE.n].region = chercheregion(tok.val)) == NULL) {
		cherchechaine(__FILE__, 28, buf, 1, tok.val); /*"Region %1 non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	switch (tok.id) {
	case FINLIGNE:
		(void) strcpy(ZONE.t[ZONE.n].specificite, "");
		ungettoken(&tok);
		break;
	case UNECOTEOUEST:
	case UNECOTESUD:
	case UNECOTENORD:
	case UNECOTEEST:
		inserecotepossible(tok.val);
		(void) strcpy(ZONE.t[ZONE.n].specificite, tok.val);
		break;
	case UNEOUVRANTE:
		cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	default:
		cherchechaine(__FILE__, 29, buf, 0); /*"Probleme definition d'une zone sur la specificite"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	}

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 30, buf, 0); /*"Manque fin de ligne apres zone"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	ZONE.t[ZONE.n].rang = rangzone++;

	assert(++ZONE.n != NZONES);
}

static void parsearmeevoisin(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE], nomzone[TAILLEMOT * 2];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 32, buf, 0); /*"Probleme definition d'un voisinarmee 1e zone"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	(void) strcpy(nomzone, tok.val);
	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTEEST:
	case UNECOTEOUEST:
	case UNECOTENORD:
	case UNECOTESUD:
		cherchechaine(__FILE__, 33, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
		informer(buf);
		(void) strcat(nomzone, tok.val);
		break;
	case UNEOUVRANTE:
		cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	default:
		ungettoken(&tok);
	}
	if ((ARMEEVOISIN.t[ARMEEVOISIN.n].zone1 = cherchezone(nomzone)) == NULL) {
		cherchechaine(__FILE__, 34, buf, 1, nomzone); /*"Zone %1 non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 35, buf, 0); /*"Probleme definition d'un voisinarmee 2e zone"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	(void) strcpy(nomzone, tok.val);
	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTEEST:
	case UNECOTEOUEST:
	case UNECOTENORD:
	case UNECOTESUD:
		cherchechaine(__FILE__, 36, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
		informer(buf);
		(void) strcat(nomzone, tok.val);
		break;
	case UNEOUVRANTE:
		cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	default:
		ungettoken(&tok);
	}
	if ((ARMEEVOISIN.t[ARMEEVOISIN.n].zone2 = cherchezone(nomzone)) == NULL) {
		cherchechaine(__FILE__, 37, buf, 1, nomzone); /*"Zone %1 non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 38, buf, 0); /*"Manque fin de ligne apres voisinarmee"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	/* Pour la table qui mmemorise les voisinages */
	TABLEVOISINAGEARMEE[ARMEEVOISIN.t[ARMEEVOISIN.n].zone1->rang][ARMEEVOISIN.t[ARMEEVOISIN.n].zone2->rang]
			= TRUE;

	assert(++ARMEEVOISIN.n != NARMEEVOISINS);
}

static void parseflottevoisin(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE], nomzone[TAILLEMOT * 2];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 40, buf, 0); /*"Probleme definition d'un voisinflotte 1e zone"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	(void) strcpy(nomzone, tok.val);
	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTEEST:
	case UNECOTEOUEST:
	case UNECOTENORD:
	case UNECOTESUD:
		cherchechaine(__FILE__, 41, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
		informer(buf);
		(void) strcat(nomzone, tok.val);
		break;
	case UNEOUVRANTE:
		cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	default:
		ungettoken(&tok);
	}
	if ((FLOTTEVOISIN.t[FLOTTEVOISIN.n].zone1 = cherchezone(nomzone)) == NULL) {
		cherchechaine(__FILE__, 42, buf, 1, nomzone); /*"Zone %1 non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 43, buf, 0); /*"Probleme definition d'un voisinflotte 2e zone"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	(void) strcpy(nomzone, tok.val);
	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTEEST:
	case UNECOTEOUEST:
	case UNECOTENORD:
	case UNECOTESUD:
		cherchechaine(__FILE__, 44, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
		informer(buf);
		(void) strcat(nomzone, tok.val);
		break;
	default:
		ungettoken(&tok);
	}
	if ((FLOTTEVOISIN.t[FLOTTEVOISIN.n].zone2 = cherchezone(nomzone)) == NULL) {
		cherchechaine(__FILE__, 45, buf, 1, nomzone); /*"Zone %1 non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 67, buf, 0); /*"Manque fin de ligne apres voisinflotte"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	/* Pour la table qui memorise les voisinages */
	TABLEVOISINAGEFLOTTE[FLOTTEVOISIN.t[FLOTTEVOISIN.n].zone1->rang][FLOTTEVOISIN.t[FLOTTEVOISIN.n].zone2->rang]
			= TRUE;

	assert(++FLOTTEVOISIN.n != NFLOTTEVOISINS);
}

/*********************************************************************************/
/*                              LES ELOIGNEMENTS                               */
/*********************************************************************************/

static void parseeloignement(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];

	gettoken(fd, &tok);
	if (tok.id != UNEARMEESUICIDE && tok.id != UNEFLOTTE) {
		cherchechaine(__FILE__, 19, buf, 0); /*"Probleme definition d'un eloignement typeunite"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	ELOIGNEMENT.t[ELOIGNEMENT.n].typeunite = (tok.id == UNEARMEESUICIDE ? ARMEE
			: FLOTTE);

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 48, buf, 0); /*"Probleme definition d'un eloignement pays"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((ELOIGNEMENT.t[ELOIGNEMENT.n].pays = cherchepays(tok.val)) == NULL) {
		cherchechaine(__FILE__, 49, buf, 1, tok.val); /*"Pays %1 non declare pour un eloignement"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 50, buf, 0); /*"Probleme definition d'un eloignement region"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((ELOIGNEMENT.t[ELOIGNEMENT.n].zone = cherchezone(tok.val)) == NULL) {
		cherchechaine(__FILE__, 51, buf, 1, tok.val); /*"Region %1  non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != NOMBRE) {
		cherchechaine(__FILE__, 52, buf, 0); /*"Probleme definition d'un eloignement valeur"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	ELOIGNEMENT.t[ELOIGNEMENT.n].valeur = tok.val2;

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 53, buf, 0); /*"Manque fin de ligne apres eloignement"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++ELOIGNEMENT.n != NELOIGNEMENTS);
}

/*********************************************************************************/
/*                              LA SITUATION INITIALE                            */
/*********************************************************************************/

static void parseunite(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE], nomzone[TAILLEMOT * 2];

	gettoken(fd, &tok);
	switch (tok.id) {
	case UNEARMEESUICIDE:
		UNITE.t[UNITE.n].typeunite = ARMEE;
		break;
	case UNEFLOTTE:
		UNITE.t[UNITE.n].typeunite = FLOTTE;
		break;
	default:
		cherchechaine(__FILE__, 55, buf, 0); /*"Probleme definition d'une unite sur le type"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 56, buf, 0); /*"Probleme definition d'une unite sur le pays"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((UNITE.t[UNITE.n].pays = cherchepays(tok.val)) == NULL) {
		cherchechaine(__FILE__, 57, buf, 1, tok.val); /*"Pays %1 non declare"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 58, buf, 0); /*"Probleme definition d'une unite sur la zone"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	(void) strcpy(nomzone, tok.val);
	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTEEST:
	case UNECOTEOUEST:
	case UNECOTENORD:
	case UNECOTESUD:
		cherchechaine(__FILE__, 59, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
		informer(buf);
		(void) strcat(nomzone, tok.val);
		break;
	case UNEOUVRANTE:
		cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	default:
		ungettoken(&tok);
	}
	if ((UNITE.t[UNITE.n].zone = cherchezone(nomzone)) == NULL) {
		cherchechaine(__FILE__, 60, buf, 1, nomzone); /*"Zone %1 non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	UNITE.t[UNITE.n].zonedepart = UNITE.t[UNITE.n].zone;

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 61, buf, 0); /*"Manque fin de ligne apres unite"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++UNITE.n != NUNITES);
}

static void parsepossession(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 63, buf, 0); /*"Probleme definition d'une possession sur le pays"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((POSSESSION.t[POSSESSION.n].pays = cherchepays(tok.val)) == NULL) {
		cherchechaine(__FILE__, 64, buf, 1, tok.val); /*"Pays %1 non declare pour une possession"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 65, buf, 0); /*"Probleme definition d'une possession sur le centre"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((POSSESSION.t[POSSESSION.n].centre = cherchecentre(tok.val)) == NULL) {
		cherchechaine(__FILE__, 66, buf, 1, tok.val); /*"Centre %1 non declare sur une possession"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 54, buf, 0); /*"Manque fin de ligne apres possession"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++POSSESSION.n != NPOSSESSIONS);
}

static void parsedelogee(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE], nomzone[TAILLEMOT * 2];
	TYPEUNITE typeunite;
	_PAYS *pays;
	_ZONE *zone;
	char nomunite[2 * TAILLEMOT];

	gettoken(fd, &tok);
	typeunite = -1; /* Evite un avertissemnt du compilateur */
	switch (tok.id) {
	case UNEARMEESUICIDE:
		typeunite = ARMEE;
		break;
	case UNEFLOTTE:
		typeunite = FLOTTE;
		break;
	default:
		cherchechaine(__FILE__, 69, buf, 0); /*"Probleme definition unite delogee sur le type"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 70, buf, 0); /*"Probleme definition unite delogee sur le pays"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((pays = cherchepays(tok.val)) == NULL) {
		cherchechaine(__FILE__, 71, buf, 1, tok.val); /*"Pays %1 non declare pour une delogee"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 72, buf, 0); /*"Probleme definition unite delogee sur la zone"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	(void) strcpy(nomzone, tok.val);
	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTEEST:
	case UNECOTEOUEST:
	case UNECOTENORD:
	case UNECOTESUD:
		cherchechaine(__FILE__, 73, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
		informer(buf);
		(void) strcat(nomzone, tok.val);
		break;
	case UNEOUVRANTE:
		cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	default:
		ungettoken(&tok);
	}
	if ((zone = cherchezone(nomzone)) == NULL) {
		cherchechaine(__FILE__, 74, buf, 1, nomzone); /*"Zone %1  non declaree pour une delogee"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	(void) strcpy(nomunite, zone->region->nom);
	(void) strcat(nomunite, zone->specificite);
	(void) strcat(nomunite, pays->nom);
	(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));
	if ((DELOGEE.t[DELOGEE.n].unite = chercheuniteavecpays(nomunite)) == NULL) {
		cherchechaine(__FILE__, 75, buf, 1, nomunite); /*"Unite %1 delogee inconnue"*/
		erreurparse(NULL, LASITUATION, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != UNBOURREAU) {
		cherchechaine(__FILE__, 76, buf, 0); /*"Manque 'BOURREAU' unite delogee"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	gettoken(fd, &tok);
	typeunite = -1; /* Evite un avertissemnt du compilateur */
	switch (tok.id) {
	case UNEARMEESUICIDE:
		typeunite = ARMEE;
		break;
	case UNEFLOTTE:
		typeunite = FLOTTE;
		break;
	default:
		cherchechaine(__FILE__, 77, buf, 0); /*"Probleme definition unite delogeante sur le type"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 78, buf, 0); /*"Probleme definition unite delogeante sur le pays"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((pays = cherchepays(tok.val)) == NULL) {
		cherchechaine(__FILE__, 79, buf, 1, tok.val); /*"Pays %1 non declare"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 80, buf, 0); /*"Probleme definition unite delogeante sur la zone de l'unite d'origine"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	(void) strcpy(nomzone, tok.val);
	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTEEST:
	case UNECOTEOUEST:
	case UNECOTENORD:
	case UNECOTESUD:
		cherchechaine(__FILE__, 81, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
		informer(buf);
		(void) strcat(nomzone, tok.val);
		break;
	case UNEOUVRANTE:
		cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	default:
		ungettoken(&tok);
	}
	if ((zone = cherchezone(nomzone)) == NULL) {
		cherchechaine(__FILE__, 82, buf, 1, nomzone); /*"Zone %1 non declaree pour une delogeante"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	(void) strcpy(nomunite, zone->region->nom);
	(void) strcat(nomunite, zone->specificite);
	(void) strcat(nomunite, pays->nom);
	(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));
	if ((DELOGEE.t[DELOGEE.n].uniteorig = chercheuniteavecpays(nomunite))
			== NULL) {
		cherchechaine(__FILE__, 83, buf, 1, nomunite); /*"Unite %1 delogeante inconnue"*/
		erreurparse(NULL, LASITUATION, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != UNEORIGINE) {
		cherchechaine(__FILE__, 84, buf, 0); /*"Manque 'ORIGINE' unite delogee"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 85, buf, 0); /*"Probleme definition unite delogeante sur la zone d'origine"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	(void) strcpy(nomzone, tok.val);
	gettoken(fd, &tok);
	switch (tok.id) {
	case UNECOTEEST:
	case UNECOTEOUEST:
	case UNECOTENORD:
	case UNECOTESUD:
		cherchechaine(__FILE__, 86, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
		informer(buf);
		(void) strcat(nomzone, tok.val);
		break;
	case UNEOUVRANTE:
		cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		break;
	default:
		ungettoken(&tok);
	}
	if ((DELOGEE.t[DELOGEE.n].zoneorig = cherchezone(nomzone)) == NULL) {
		cherchechaine(__FILE__, 87, buf, 1, nomzone); /*"Zone %1 non declaree pour une origine de delogeage"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 88, buf, 0); /*"Manque fin de ligne apres delogee"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++DELOGEE.n != NDELOGEES);
}

static void parseinterdit(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 90, buf, 0); /*"Probleme definition d'un interdit sur la region"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((INTERDIT.t[INTERDIT.n].region = chercheregion(tok.val)) == NULL) {
		cherchechaine(__FILE__, 91, buf, 1, tok.val); /*"Region interdite en retraite %1 non declaree"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 92, buf, 0); /*"Manque fin de ligne apres interdit"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	assert(++INTERDIT.n != NINTERDITS);
}


static void parseanneezero(FILE *fd) {
	TOKEN tok;
	char buf[TAILLEMESSAGE];


	gettoken(fd, &tok);
	if (tok.id != NOMBRE) {
		cherchechaine(__FILE__, 270, buf, 0); /*"Manque l'anneezero"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	ANNEEZERO = tok.val2;

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 271, buf, 0); /*"Manque fin de ligne apres annezero"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

}

static void parsesaison(FILE *fd) {
	TOKEN tok;
	int annee, saison;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	gettoken(fd, &tok);
	saison = -1; /* Evite un avertissemnt du compilateur */
	switch (tok.id) {
	case UNPRINTEMPS:
		saison = PRINTEMPS;
		break;
	case UNETE:
		saison = ETE;
		break;
	case UNAUTOMNE:
		saison = AUTOMNE;
		break;
	case UNHIVER:
		saison = HIVER;
		break;
	case UNBILAN:
		saison = BILAN;
		break;
	default:
		cherchechaine(__FILE__, 94, buf, 0); /*"Probleme definition d'une saison sur la saison elle meme"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != NOMBRE) {
		cherchechaine(__FILE__, 95, buf, 0); /*"Manque l'annee pour la saison"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	annee = tok.val2;
	if (annee < ANNEEZERO+1 || annee > ANNEEZERO+MAXIMUMANNEE) {
		(void) sprintf(bufn1, "%d", annee);
		cherchechaine(__FILE__, 96, buf, 1, bufn1); /*"%1 : Annee saison invraisemblable"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	SAISON = ((annee - ANNEEZERO) * 5) + saison; /* variable globale */

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 97, buf, 0); /*"Manque fin de ligne apres saison"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

}

static void parsesaisonmodif(FILE *fd) {
	TOKEN tok;
	int annee, saison;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	gettoken(fd, &tok);
	if (tok.id != UNHIVER) {
		cherchechaine(__FILE__, 98, buf, 0); /*"Probleme definition d'une saisonmodif sur la saison elle meme (HIVER)"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != NOMBRE) {
		cherchechaine(__FILE__, 99, buf, 0); /*"Manque l'annee pour la saisonmodif"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	saison = 3; /* hiver */
	annee = tok.val2;
	if (annee < ANNEEZERO || annee > ANNEEZERO+MAXIMUMANNEE) {
		(void) sprintf(bufn1, "%d", annee);
		cherchechaine(__FILE__, 100, buf, 1, bufn1); /*"%1 : Annee saison modif invraisemblable"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	SAISONMODIF = ((annee - ANNEEZERO) * 5) + saison; /* variable globale */

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 101, buf, 0); /*"Manque fin de ligne apres saison modif"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}
}

static void parsedisparition(FILE *fd) {
	TOKEN tok;
	int annee;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	gettoken(fd, &tok);
	if (tok.id != CHAINE) {
		cherchechaine(__FILE__, 261, buf, 0); /*"Probleme definition d'une disparition sur le pays"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}
	if ((DISPARITION.t[DISPARITION.n].pays = cherchepays(tok.val)) == NULL) {
		cherchechaine(__FILE__, 262, buf, 1, tok.val); /*"Pays %1 non declare pour une disparition"*/
		erreurparse(NULL, LACARTE, FALSE, buf);
	}

	gettoken(fd, &tok);
	if (tok.id != NOMBRE) {
		cherchechaine(__FILE__, 263, buf, 0); /*"Manque l'annee pour la disparition"*/
		erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
	}

	annee = tok.val2;
	if (annee < ANNEEZERO+1 || annee > ANNEEZERO + (SAISON / NSAISONS)) {
		(void) sprintf(bufn1, "%d", annee);
		cherchechaine(__FILE__, 264, buf, 1, bufn1); /*"%1 : Annee disparition invraisemblable"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	DISPARITION.t[DISPARITION.n].annee = annee;

	gettoken(fd, &tok);
	if (tok.id != FINLIGNE) {
		cherchechaine(__FILE__, 265, buf, 0); /*"Manque fin de ligne apres disparition"*/
		erreurparse(NULL, SYNTAXIQUE, FALSE, buf);
	}

	assert(++DISPARITION.n != NDISPARITIONS);
}

static void verifdisparitions(void) {
	_PAYS *p;
	_DISPARITION *q;
	_POSSESSION *r;
	char buf[TAILLEMESSAGE];

	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++) {

		for (q = DISPARITION.t; q < DISPARITION.t + DISPARITION.n; q++) {
			if(q->pays == p)
				break;
		}

		/* disparu */
		if(q < DISPARITION.t + DISPARITION.n) {

			/* cherche si possede un centre */
			for (r = POSSESSION.t; r < POSSESSION.t + POSSESSION.n; r++) {
				if(r->pays == p) {
					cherchechaine(__FILE__, 267, buf, 1, p->nom); /*"Pays %1 disparu mais possede au moins centre"*/
					erreurparse(NULL, LASITUATION, FALSE, buf);
				}
			}

		/* pas disparu */
		} else {

			/* cherche si possede pas de  centre */
			for (r = POSSESSION.t; r < POSSESSION.t + POSSESSION.n; r++) {
				if(r->pays == p)
					break;
			}

			if(r == POSSESSION.t + POSSESSION.n) {

				if (OPTIONw) {
					cherchechaine(__FILE__, 268, buf, 1, p->nom); /*"Pays %1 sans centre mais pas disparu (rectifi�)"*/
					avertir(buf);
				}

				/* insere cette information */
				DISPARITION.t[DISPARITION.n].pays = p;
				DISPARITION.t[DISPARITION.n].annee = ANNEEZERO + (SAISON / NSAISONS);
				DISPARITION.n++;

				assert(DISPARITION.n != NDISPARITIONS);

			}
		}
	}
}


/*********************************************************************************/
/*                          ROUTINES VISIBLES DE L'EXTERIEUR                     */
/*********************************************************************************/

void parsecarte(char *nomfic) {
	FILE *fd;
	TOKEN tok;
	char buf[TAILLEMESSAGE];

	COTEPOSS.n = 0;

	if ((fd = fopen(nomfic, "r")) == NULL) {
		cherchechaine(__FILE__, 102, buf, 1, nomfic); /*"Impossible de lire la carte : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	lecture = CARTE;
	noligne = 1;

	for (;;) {
		gettoken(fd, &tok);
		switch (tok.id) {
		case FINLIGNE:
			continue;
		case FINFICHIER:
			(void) fclose(fd);
			return;
		case UNEANNEEZERO:
			parseanneezero(fd);
			break;
		case UNPAYS:
			parsepays(fd);
			break;
		case UNEREGION:
			parseregion(fd);
			break;
		case UNCENTRE:
			parsecentre(fd);
			break;
		case UNCENTREDEPART:
			parsecentredepart(fd);
			break;
		case UNEZONE:
			parsezone(fd);
			break;
		case UNFLOTTEVOISIN:
			parseflottevoisin(fd);
			break;
		case UNARMEEVOISIN:
			parsearmeevoisin(fd);
			break;
		case UNELOIGNEMENT:
			parseeloignement(fd);
			break;
		default:
			cherchechaine(__FILE__, 103, buf, 0); /*"Chaine inattendue mettez un ';'"*/
			erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		}
	}
}


void parsesituation(char *nomfic) {
	FILE *fd;
	TOKEN tok;
	ETATAUTOSITU etat;
	char buf[TAILLEMESSAGE];

	if ((fd = fopen(nomfic, "r")) == NULL) {
		cherchechaine(__FILE__, 106, buf, 1, nomfic); /*"Impossible de lire la situation initiale : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	lecture = SITUATION;
	noligne = 1;

	etat = PRESAISON;
	for (;;) {
		gettoken(fd, &tok);
		switch (tok.id) {
		case FINLIGNE:
			continue;
		case FINFICHIER:
			if (etat != NORMAL) {
				cherchechaine(__FILE__, 107, buf, 0); /*"Fin de fichier impromptue"*/
				erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			(void) fclose(fd);
			verifdisparitions();
			return;
		case UNESAISON:
			if (etat != PRESAISON) {
				cherchechaine(__FILE__, 108, buf, 0); /*"Saison debutant la situation impromptue"*/
				erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			parsesaison(fd);
			etat = PRESAISONMODIF;
			break;
		case UNESAISONMODIF:
			if (etat != PRESAISONMODIF) {
				cherchechaine(__FILE__, 109, buf, 0); /*"Saisonmodif apres la saison impronmptue"*/
				erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			parsesaisonmodif(fd);
			etat = NORMAL;
			break;
		case UNEUNITE:
			if (etat != NORMAL) {
				cherchechaine(__FILE__, 110, buf, 0); /*"Oubli de saison ou saisonmodif (ou les deux) avant une unite"*/
				erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			parseunite(fd);
			break;
		case UNEPOSSESSION:
			if (etat != NORMAL) {
				cherchechaine(__FILE__, 111, buf, 0); /*"Oubli de saison ou saisonmodif (ou les deux) avant une possesson"*/
				erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			parsepossession(fd);
			break;
		case UNEDELOGEE:
			if (etat != NORMAL) {
				cherchechaine(__FILE__, 112, buf, 0); /*"Oubli de saison ou saisonmodif (ou les deux) avant une delogee"*/
				erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			if (!(SAISON % 5 == 1 || SAISON % 5 == 3)) {
				cherchechaine(__FILE__, 113, buf, 0); /*"Unite delogee : pas la saison !"*/
				erreurparse(NULL, LASITUATION, FALSE, buf);
			}
			parsedelogee(fd);
			break;
		case UNINTERDIT:
			if (etat != NORMAL) {
				cherchechaine(__FILE__, 114, buf, 0); /*"Oubli de saison ou saisonmodif (ou les deux) avant un interdit"*/
				erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			if (!(SAISON % 5 == 1 || SAISON % 5 == 3)) {
				cherchechaine(__FILE__, 115, buf, 0); /*"Zone interdite en retraite : pas la saison !"*/
				erreurparse(NULL, LASITUATION, FALSE, buf);
			}
			parseinterdit(fd);
			break;
		case UNEDISPARITION:
			if (etat != NORMAL) {
				cherchechaine(__FILE__, 266, buf, 0); /*"Oubli de saison ou saisonmodif (ou les deux) avant une dispariton"*/
				erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			parsedisparition(fd);
			break;
		default:
			cherchechaine(__FILE__, 116, buf, 0); /*"Chaine inattendue mettez un ';'"*/
			erreurparse(NULL, SYNTAXIQUE, tok.id == FINLIGNE, buf);
		}
	}
}

/************************* PARTIE BLINDEE ***************************/

void parsemouvements(char *nomfic) {
	FILE *fd;
	TOKEN tok, tok2;
	ETATAUTOMOUV etat;
	char buf[TAILLEMESSAGE * 2], nomunite[2 * TAILLEMOT],
			nomzone[TAILLEMOT * 2];
	BOOL typeunitepasspresent, paysunitepasspresent;
	TYPEUNITE typeunite, typeunitepass;
	TYPEMOUVEMENT typemouvement;
	_ZONE *zonedest, *zonedest2;
	_UNITE *unite, *unitepass, *unitepasstrouv1, *unitepasstrouv2;
	_PAYS *pays, *paysunitepass, *paysprec;
	int ordrespays;
	BOOL ouverte,zonetrouvee;
	_COTEPOSS *p;
	int nbcotesposs;

	if ((fd = fopen(nomfic, "r")) == NULL) {
		cherchechaine(__FILE__, 117, buf, 1, nomfic); /*"Impossible de lire les ordres de mouvement : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	pays = NULL;
	lecture = ORDRES;
	(void) strcpy(image, "");
	changeligne = FALSE;
	noligne = 1;

	etat = MOUVINIT;

	typeunitepasspresent = -1; /* Evite un avertissemnt du compilateur */
	paysunitepasspresent = -1; /* Evite un avertissemnt du compilateur */
	typeunite = -1; /* Evite un avertissemnt du compilateur */
	typeunitepass = -1; /* Evite un avertissemnt du compilateur */
	typemouvement = -1; /* Evite un avertissemnt du compilateur */
	zonedest = NULL; /* Evite un avertissemnt du compilateur */
	unite = NULL; /* Evite un avertissemnt du compilateur */
	unitepass = NULL; /* Evite un avertissemnt du compilateur */
	paysunitepass = NULL; /* Evite un avertissemnt du compilateur */
	ordrespays = -1; /* Evite un avertissemnt du compilateur */

	for (;;) {
		gettoken(fd, &tok);
		switch (etat) {

		case MOUVINIT:
			switch (tok.id) {
			case FINFICHIER:
				cherchechaine(__FILE__, 118, buf, 0); /*"Mouvements : Pas d'ordre  dans le fichier"*/
				avertir(buf);
				(void) fclose(fd);
				return;
			case FINLIGNE:
				continue;
			case CHAINE:
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 119, buf, 1, tok.val); /*"Mouvements : pays %1 inconnu"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				ordrespays = 0;
				etat = MOUV11;
				break;
			default:
				cherchechaine(__FILE__, 120, buf, 0); /*"Mouvements : nom de pays attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case MOUV11:
			if (tok.id != FINLIGNE) {
				cherchechaine(__FILE__, 223, buf, 0); /*"Aller a la ligne apres le nom de pays"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			etat = MOUV0;
			ungettoken(&tok);
			break;

		case MOUV0:
			switch (tok.id) {
			case FINLIGNE:
				continue;
			case FINFICHIER:
				if (ordrespays == 0) {
					cherchechaine(__FILE__, 121, buf, 1, pays->nom); /*"Mouvements : pays %1 declare mais sans ordres"*/
					avertir(buf);
				}
				(void) fclose(fd);
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
				paysprec = pays;
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 122, buf, 1, tok.val); /*"Pays %1 inconnu ou mauvais debut d'ordre de mouvement"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if (paysprec != NULL && ordrespays == 0) {
					cherchechaine(__FILE__, 123, buf, 1, paysprec->nom); /*"Mouvements : pays %1 declare mais sans ordres"*/
					avertir(buf);
				}
				ordrespays = 0;
				break;
			case UNERETRAITE:
				cherchechaine(__FILE__, 231, buf, 0); /*"Il est preferable d'utiliser '-' plutot que 'R' pour retirer une unite"*/
				informer(buf);
				cherchechaine(__FILE__, 168, buf, 0); /*"Ce n'est pas une phase d'ajustements"*/
				erreurparse(pays, LASITUATION, FALSE, buf);
				break;
			case UNAJOUT:
			case UNREMOVE:
			case UNEATTAQUESUPPRESSION:
				cherchechaine(__FILE__, 168, buf, 0); /*"Ce n'est pas une phase d'ajustements"*/
				erreurparse(pays, LASITUATION, FALSE, buf);
				break;
			default:
				cherchechaine(__FILE__, 124, buf, 0); /*"Type d'unite 'A' ou 'F' ou nom de pays attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case MOUV1:
			if (tok.id != CHAINE) {
				cherchechaine(__FILE__, 125, buf, 0); /*"Zone de l'unite active d'un mouvement attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			(void) strcpy(nomzone, tok.val);
			ouverte = FALSE;
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
				cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
				informer(buf);
				ouverte = TRUE;
				break;
			case UNSLASH:
				cherchechaine(__FILE__, 25, buf, 0); /*"Ne pas utiliser de slash '/' pour les c�tes"*/
				informer(buf);
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
				cherchechaine(__FILE__, 126, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
				informer(buf);
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				if (!ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				break;
			default:
				if (ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				ungettoken(&tok);
			}

			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 127, buf, 1, nomzone); /*"Zone %1 inconnue"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			(void) strcpy(nomunite, zonedest->region->nom);
			(void) strcat(nomunite, zonedest->specificite);
			(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));
			if ((unite = chercheunite(nomunite)) == NULL) {
				if (typeunite == FLOTTE && !strcmp(zonedest->specificite, "")
						&& cotesexistent(zonedest)) {
					cherchechaine(__FILE__, 237, buf, 0); /*"Attention : si la province a des cotes, la preciser pour une flotte en unite active ordre mouvement"*/
					avertir(buf);
					for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
						(void) strcpy(nomunite, zonedest->region->nom);
						(void) strcat(nomunite, p->nom);
						(void) strcat(nomunite, "F");
						if ((unite = chercheunite(nomunite)) != NULL)
							break;
					}
				}
				if (typeunite == ARMEE && strcmp(zonedest->specificite, "")
					&& cotesexistent(zonedest)) {
					cherchechaine(__FILE__, 259, buf, 0); /*"Attention : si la province a des cotes, ne pas la preciser pour une armee "*/
					avertir(buf);
				}
				if (unite == NULL) {
					if (!compatibles(typeunite, zonedest)) {
						cherchechaine(__FILE__, 247, buf, 0); /*"Une telle unite ne peut se trouver a cet endroit"*/
						erreurparse(pays, LESREGLES, FALSE, buf);
					}
					(void) strcpy(nomunite, zonedest->region->nom);
					(void) strcat(nomunite, zonedest->specificite);
					(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));
					cherchechaine(__FILE__, 128, buf, 1, nomunite); /*"Unite %1 active inconnue"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}
			}
			if (unite->pays != pays) {
				cherchechaine(__FILE__, 129, buf, 1, nomunite); /*"Unite %1 active pas du pays du donneur d'ordre"*/
				erreurparse(pays, LASITUATION, FALSE, buf);
			}

			etat = MOUV2;
			break;

		case MOUV2:
			switch (tok.id) {
			case UNSTAND:
				typemouvement = STAND;
				etat = MOUVFIN;
				break;
			case UNEATTAQUESUPPRESSION:
				typemouvement = ATTAQUE;
				etat = MOUV3;
				break;
			case UNSOUTIEN:
				typemouvement = STAND; /* doit etre defini */
				etat = MOUV8; /* typemouvement non encore decelable */
				break;
			case UNCONVOI:
				if (unite->typeunite != FLOTTE) {
					cherchechaine(__FILE__, 146, buf, 0); /*"Seules les flottes convoient"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				typemouvement = CONVOI;
				etat = MOUV8;
				break;
			case UNSUICIDE:
			case UNEARMEESUICIDE:
			case UNERETRAITE:
				cherchechaine(__FILE__, 169, buf, 0); /*"Il s'agit pas d'une phase retraites"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				break;
			default:
				cherchechaine(__FILE__, 130, buf, 0); /*"Ordre unite active '-' 'H' 'S' ou 'C' attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				break;
			}
			break;

		case MOUV3:
			if (tok.id == UNSTAND) {
				cherchechaine(__FILE__, 46, buf, 0); /*"Ne pas utiliser la construction '- H'"*/
				avertir(buf);
				typemouvement = STAND;
				etat = MOUVFIN;
				break;
			}
			if (tok.id != CHAINE) {
				cherchechaine(__FILE__, 131, buf, 0); /*"Zone unite passive attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			(void) strcpy(nomzone, tok.val);
			ouverte = FALSE;
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
				cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
				informer(buf);
				ouverte = TRUE;
				break;
			case UNSLASH:
				cherchechaine(__FILE__, 25, buf, 0); /*"Ne pas utiliser de slash '/' pour les c�tes"*/
				informer(buf);
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
				cherchechaine(__FILE__, 132, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
				informer(buf);
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				if (!ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				break;
			default:
				if (ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				ungettoken(&tok);
			}

			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 133, buf, 1, nomzone); /*"Zone %1 inconnue"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			/* Elements superflus convoi d'armee */

			if (typeunite == ARMEE) {
				gettoken(fd, &tok);
				switch (tok.id) {
				case UNEATTAQUESUPPRESSION:/* Pour ceux qui fournissent un chemin de convoi explicite */
					cherchechaine(__FILE__, 257, buf, 0); /*"Pas de chemin de convoi...""*/
					avertir(buf);
					break;
					/* Pour ceux qui fournissent un chemin de convoi */
				case UNVIA:
					gettoken(fd, &tok2);
					switch (tok2.id) {
					case UNCONVOY:
						cherchechaine(__FILE__, 258, buf, 0); /*"Pas de via convoy"*/
						avertir(buf);
						break;
					default:
						ungettoken(&tok2);
						ungettoken(&tok);
						break;
					}
					break;
				default:
					ungettoken(&tok);
					break;
				}
			}

			etat = MOUVFIN;
			break;

		case MOUV6:
			switch (tok.id) {
			case UNSTAND:
				switch (typemouvement) {
				case STAND:
					typemouvement = SOUTIENDEF; /* enfin ! */
					cherchechaine(__FILE__, 224, buf, 0); /*"Le 'H' sur un soutien passif est superflu"*/
					informer(buf);
					break;
				case CONVOI:
					cherchechaine(__FILE__, 135, buf, 0); /*"Probleme, manque la destination du convoi "*/
					erreurparse(pays, SYNTAXIQUE, FALSE, buf);
					break;
				default:
					assert(FALSE); /* erreur interne */
				}
				etat = MOUVFIN;
				break;
			case FINFICHIER:
			case FINLIGNE:
				ungettoken(&tok);
				switch (typemouvement) {
				case STAND:
					typemouvement = SOUTIENDEF; /* enfin ! */
					break;
				case CONVOI:
					cherchechaine(__FILE__, 135, buf, 0); /*"Probleme, manque la destination du convoi "*/
					erreurparse(pays, SYNTAXIQUE, FALSE, buf);
					break;
				default:
					assert(FALSE); /* erreur interne */
				}
				etat = MOUVFIN;
				break;
			case UNEATTAQUESUPPRESSION:
				switch (typemouvement) {
				case STAND: /* i.e. SOUTIENOFF ou SOUTIENDEF */
					typemouvement = SOUTIENOFF; /* enfin ! */
					break;
				case CONVOI:
					break;
				default:
					assert(FALSE); /* erreur interne */
				}
				etat = MOUV7;
				break;
			default:
				cherchechaine(__FILE__, 136, buf, 0); /*"Ordre unite passive '-' ou fin de ligne attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case MOUV7:
			if (tok.id != CHAINE) {
				if (typemouvement != CONVOI) {
					cherchechaine(__FILE__, 242, buf, 0); /*"Attend la d�signation de la destination l'unit� soutenue offensivement"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				} else {
					cherchechaine(__FILE__, 243, buf, 0); /*"Attend la d�signation de la destination de l'unit� convoy�e"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
			}
			(void) strcpy(nomzone, tok.val);
			ouverte = FALSE;
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
				cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
				informer(buf);
				ouverte = TRUE;
				break;
			case UNSLASH:
				cherchechaine(__FILE__, 25, buf, 0); /*"Ne pas utiliser de slash '/' pour les c�tes"*/
				informer(buf);
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
				cherchechaine(__FILE__, 138, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
				informer(buf);
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				if (!ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				break;
			default:
				if (ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				ungettoken(&tok);
			}

			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 139, buf, 1, nomzone); /*"Zone %1 inconnue"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			etat = MOUVFIN;
			break;

		case MOUV8:
			if ((tok.id == CHAINE) && (paysunitepass = chercheadjectifpays(
					tok.val)) != NULL) {
				paysunitepasspresent = TRUE;
			} else {
				ungettoken(&tok);
				paysunitepasspresent = FALSE;
			}
			etat = MOUV9;
			break;

		case MOUV9:
			switch (tok.id) {
			case UNEARMEESUICIDE:
				typeunitepasspresent = TRUE;
				typeunitepass = ARMEE;
				break;
			case UNEFLOTTE:
				typeunitepasspresent = TRUE;
				typeunitepass = FLOTTE;
				break;
			default:
				typeunitepasspresent = FALSE;
				ungettoken(&tok);
				break;
			}
			etat = MOUV10;
			break;

		case MOUV10:
			if (tok.id != CHAINE) {
				if (typemouvement != CONVOI) {
					cherchechaine(__FILE__, 240, buf, 0); /*"Attend la d�signation de l'unit� soutenue offensivement"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				} else {
					cherchechaine(__FILE__, 241, buf, 0); /*"Attend la d�signation de l'unit� convoy�e"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
			}
			(void) strcpy(nomzone, tok.val);
			ouverte = FALSE;
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
				cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
				informer(buf);
				ouverte = TRUE;
				break;
			case UNSLASH:
				cherchechaine(__FILE__, 25, buf, 0); /*"Ne pas utiliser de slash '/' pour les c�tes"*/
				informer(buf);
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
				cherchechaine(__FILE__, 140, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
				informer(buf);
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				if (!ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				break;
			default:
				if (ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				ungettoken(&tok);
			}

			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 141, buf, 1, nomzone); /*"Zone %1 inconnue ou pays ou type"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}

			if (typeunitepasspresent) { /* Le type de l'unite passive a ete mis */

				(void) strcpy(nomunite, zonedest->region->nom);
				(void) strcat(nomunite, zonedest->specificite);
				(void) strcat(nomunite, (typeunitepass == ARMEE ? "A" : "F"));
				if ((unitepass = chercheunite(nomunite)) == NULL) {
					if (typeunitepass == FLOTTE && !strcmp(
							zonedest->specificite, "") && cotesexistent(
							zonedest)) {
						cherchechaine(__FILE__, 234, buf, 0); /*"Attention : si la province a des cotes, la preciser pour une flotte en unite passive d'un soutien"*/
						avertir(buf);
						for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
							(void) strcpy(nomunite, zonedest->region->nom);
							(void) strcat(nomunite, p->nom);
							(void) strcat(nomunite, "F");
							if ((unitepass = chercheunite(nomunite)) != NULL)
								break;
						}
					}
					if (unitepass == NULL) {
						(void) strcpy(nomunite, zonedest->region->nom);
						(void) strcat(nomunite, zonedest->specificite);
						(void) strcat(nomunite, (typeunitepass == ARMEE ? "A"
								: "F"));
						cherchechaine(__FILE__, 142, buf, 1, nomunite); /*"Unite %1 passive inconnue"*/
						erreurparse(pays, LASITUATION, FALSE, buf);
					}
				}

			} else { /* Le type de l'unite passive a ete omis */

				/* Recherche d'arm�e */
				(void) strcpy(nomunite, zonedest->region->nom);
				(void) strcat(nomunite, zonedest->specificite);
				(void) strcat(nomunite, "A");
				unitepasstrouv1 = chercheunite(nomunite);

				/* Recherche de flotte */
				(void) strcpy(nomunite, zonedest->region->nom);
				(void) strcat(nomunite, zonedest->specificite);
				(void) strcat(nomunite, "F");
				unitepasstrouv2 = chercheunite(nomunite);

				/* Pas trouve ni arm�e ni flotte */
				if (unitepasstrouv1 == NULL && unitepasstrouv2 == NULL) {

					if (!strcmp(zonedest->specificite, "") && cotesexistent(
							zonedest)) {
						cherchechaine(__FILE__, 234, buf, 0); /*"Attention : si la province a des cotes, la preciser pour une flotte en unite passive d'un soutien"*/
						avertir(buf);
					}
					for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
						(void) strcpy(nomunite, zonedest->region->nom);
						(void) strcat(nomunite, p->nom);
						(void) strcat(nomunite, "F");
						if ((unitepasstrouv2 = chercheunite(nomunite)) != NULL)
							break;
					}
					if (unitepasstrouv2 == NULL) {
						cherchechaine(__FILE__, 143, buf, 2,
								zonedest->region->nom, zonedest->specificite); /*"Pas de d'unite possible en %1%2"*/
						erreurparse(pays, LASITUATION, FALSE, buf);
					}
				}

				/* Trouv� � la fois arm�e et flotte (possible grace aux synonymes) */
				if (unitepasstrouv1 != NULL && unitepasstrouv2 != NULL) {
					cherchechaine(__FILE__, 228, buf, 2, zonedest->region->nom,
							zonedest->specificite); /*"Ambiguite sur l'unite possible en %1%2"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}

				if (unitepasstrouv1 != NULL) {
					typeunitepass = ARMEE;
					unitepass = unitepasstrouv1;
				} else {
					typeunitepass = FLOTTE;
					unitepass = unitepasstrouv2;
				}

			}

			if (paysunitepasspresent && unitepass->pays != paysunitepass) {
				cherchechaine(__FILE__, 144, buf, 0); /*"Le pays precise n'est pas celui de l'unite soutenue ou convoyee"*/
				erreurparse(pays, LASITUATION, FALSE, buf);
			}

			etat = MOUV6;
			break;

		case MOUVFIN:
			if (tok.id != FINLIGNE && tok.id != FINFICHIER) {
				cherchechaine(__FILE__, 145, buf, 0); /*"El�ments superflus dans un ordre de mouvement"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			ungettoken(&tok); /* Se remet sur la bonne ligne */
			switch (typemouvement) {

			case STAND:
				/* Forcement correct ! */
				break;

			case CONVOI:
				if (unitepass->typeunite != ARMEE) {
					cherchechaine(__FILE__, 147, buf, 0); /*"Seules les armees sont convoyees"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (unite->zone->typezone != MER) {
					cherchechaine(__FILE__, 148, buf, 0); /*"Seules les flottes en mer convoient"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (unitepass->zone->typezone != COTE) {
					cherchechaine(__FILE__, 149, buf, 0); /*"Seules les armees en cote sont convoyees"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (strcmp(zonedest->specificite, "")) {
					cherchechaine(__FILE__, 194, buf, 0); /*"Attention : pas de cote pour une armee"*/
					avertir(buf);
					cherchechaine(__FILE__, 152, buf, 0); /*"Incompatibilite de types entre unite passive et zone destination du soutien"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (!peutconvoyer(unite, unitepass, NULL)) {
					cherchechaine(__FILE__, 233, buf, 0); /*"La flotte n'a pas acces � l'arm�e"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}
				if (!convoipossible(NULL, unitepass->zone, zonedest)) {
					cherchechaine(__FILE__, 150, buf, 0); /*"Pas de convoi possible de l'unite passive a la zone destination"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}
				if (!peutconvoyer(unite, unitepass, zonedest)) {
					cherchechaine(__FILE__, 250, buf, 1, unite->zone->region); /*"La flotte %1 est inutile au convoi"*/
					avertir(buf);
				}
				break;

			case SOUTIENOFF:
				if (!compatibles(unitepass->typeunite, zonedest)) {
					zonetrouvee = FALSE;
					/* Cas ou on s'est abstenu de preciser la cote pour une flotte */
					if (unitepass->typeunite == FLOTTE && !strcmp(
							zonedest->specificite, "") && cotesexistent(
							zonedest)) {
						cherchechaine(__FILE__, 151, buf, 0); /*"Attention : si la region a des cotes, la preciser pour une flotte lors d'un soutien offensif"*/
						avertir(buf);
						nbcotesposs = 0;
						/* On va essayer de trouver la cote quand meme */
						for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
							(void) strcpy(nomzone, zonedest->region->nom);
							(void) strcat(nomzone, p->nom);
							if (((zonedest2 = cherchezone(nomzone)) != NULL)
									&& compatibles(unitepass->typeunite,
											zonedest2) && flottevoisin(
									unitepass->zone, zonedest2)) {
								nbcotesposs++;
								zonedest = zonedest2;
							}
						}
						/* Exactement une seule cote possible : l'ambiguite est levee */
						if(nbcotesposs == 1)
							zonetrouvee = TRUE;
					}
					/* Cas de zone parasite pour une armee (pour justifier l'erreur qui va suivre) */
					if (unitepass->typeunite == ARMEE && strcmp(
							zonedest->specificite, "")) {
						cherchechaine(__FILE__, 194, buf, 0); /*"Attention : pas de cote pour une armee"*/
						avertir(buf);
					}
					/* On a pas trouve la zone par deduction */
					if (!zonetrouvee) {
						cherchechaine(__FILE__, 152, buf, 0); /*"Incompatibilite de types entre unite passive et zone destination du soutien"*/
						erreurparse(pays, LESREGLES, FALSE, buf);
					}
				}
				/* Signaler que soutien valable pour toutes les cotes */
				if (unitepass->typeunite == FLOTTE &&  cotesexistent(zonedest)) {
					/* On va compter les cotes */
					nbcotesposs = 0;
					for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
						(void) strcpy(nomzone, zonedest->region->nom);
						(void) strcat(nomzone, p->nom);
						if (((zonedest2 = cherchezone(nomzone)) != NULL)
								&& compatibles(unitepass->typeunite,
										zonedest2) && flottevoisin(
								unitepass->zone, zonedest2))
							nbcotesposs++;
					}
					/* Plus d'une cote : on explique que le soutien est "generique" */
					if(nbcotesposs > 1) {
						cherchechaine(__FILE__, 89, buf, 0); /*"Attention : soutien valable pour toutes les cotes !"*/
						avertir(buf);
					}
				}
				if (unite == unitepass) {
					cherchechaine(__FILE__, 153, buf, 0); /*"L'unite se soutient offensivement elle meme (!)"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (unite->zone->region == zonedest->region) {
					cherchechaine(__FILE__, 154, buf, 0); /*"L'unite soutient contre elle meme (!)"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (unitepass->zone->region == zonedest->region) {
					if (unitepass->zone != zonedest) {
						cherchechaine(__FILE__, 244, buf, 0); /*"Attention : on ne peut aller d'une cote � une autre"*/
						informer(buf);
					}
					cherchechaine(__FILE__, 155, buf, 0); /*"L'unite soutient pour faire du sur place (!)"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if ((unite->typeunite == FLOTTE) && !(flottevoisin(unite->zone,
						zonedest)
						|| contactsoutienflotte(unite->zone, zonedest))) {
					cherchechaine(__FILE__, 156, buf, 0); /*"La flotte active n'a pas acces a la zone destination"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if ((unite->typeunite == ARMEE)
						&& !(armeevoisin(unite->zone, zonedest)
								|| contactsoutienarmee(unite->zone, zonedest))) {
					cherchechaine(__FILE__, 157, buf, 0); /*"L'armee active n'a pas acces a la zone destination"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if ((unitepass->typeunite == FLOTTE) && !flottevoisin(
						unitepass->zone, zonedest)) {
					cherchechaine(__FILE__, 158, buf, 0); /*"L'unite passive n'a pas acces a la zone destination"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if ((unitepass->typeunite == ARMEE) && !(armeevoisin(
						unitepass->zone, zonedest) || convoipossible(NULL,
						unitepass->zone, zonedest))) {
					cherchechaine(__FILE__, 159, buf, 0); /*"L'unite passive n'a pas acces (meme par convoi) a la zone destination"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				break;

			case ATTAQUE:
				if (!compatibles(unite->typeunite, zonedest)) {
					zonetrouvee = FALSE;
					if (unite->typeunite == FLOTTE && !strcmp(
							zonedest->specificite, "") && cotesexistent(
							zonedest)) {
						cherchechaine(__FILE__, 160, buf, 0); /*"Attention : si la region a des cotes, la preciser pour une flotte lors d'un mouvement"*/
						avertir(buf);
						/* On va essayer de trouver la cote quand meme */
						nbcotesposs = 0;
						for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
							(void) strcpy(nomzone, zonedest->region->nom);
							(void) strcat(nomzone, p->nom);
							if (((zonedest2 = cherchezone(nomzone)) != NULL)
									&& compatibles(unite->typeunite, zonedest2)
									&& flottevoisin(unite->zone, zonedest2)) {
								nbcotesposs++;
								zonedest = zonedest2;
							}
						}
						/* Exactement une seule cote possible : l'ambiguite est levee */
						if(nbcotesposs == 1)
							zonetrouvee = TRUE;
					}
					if (unite->typeunite == ARMEE && strcmp(
							zonedest->specificite, "")) {
						cherchechaine(__FILE__, 194, buf, 0); /*"Attention : pas de cote pour une armee"*/
						avertir(buf);
					}
					/* On a pas trouve la zone par deduction */
					if (!zonetrouvee) {
						cherchechaine(__FILE__, 161, buf, 0); /*"Incompatibilite de types entre unite active et zone destination de l'attaque"*/
						erreurparse(pays, LESREGLES, FALSE, buf);
					}
				}
				if (unite->zone->region == zonedest->region) {
					if (unite->zone != zonedest) {
						cherchechaine(__FILE__, 244, buf, 0); /*"Attention : on ne peut aller d'une cote � une autre"*/
						informer(buf);
					}
					cherchechaine(__FILE__, 162, buf, 0); /*"L'unite tente de faire du surplace (!)"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (unite->typeunite == FLOTTE && !flottevoisin(unite->zone,
						zonedest)) {
					cherchechaine(__FILE__, 163, buf, 0); /*"L'unite n'a pas acces a la zone"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if (unite->typeunite == ARMEE && !(armeevoisin(unite->zone,
						zonedest)
						|| convoipossible(NULL, unite->zone, zonedest))) {
					cherchechaine(__FILE__, 164, buf, 0); /*"L'unite n'a pas acces (meme par convoi) a la zone"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				break;

			case SOUTIENDEF:
				if (unite == unitepass) {
					cherchechaine(__FILE__, 165, buf, 0); /*"L'unite se soutient defensivement elle meme (!)"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (unite->typeunite == FLOTTE && !(flottevoisin(unite->zone,
						unitepass->zone) || contactsoutienflotte(unite->zone,
						unitepass->zone))) {
					cherchechaine(__FILE__, 166, buf, 0); /*"La flotte n'a pas acces a la zone de celle soutenue"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if ((unite->typeunite == ARMEE) && !(armeevoisin(unite->zone,
						unitepass->zone) || contactsoutienarmee(unite->zone,
						unitepass->zone))) {
					cherchechaine(__FILE__, 167, buf, 0); /*"L'armee n'a pas acces a la zone de celle soutenue"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				break;
			}
			MOUVEMENT.t[MOUVEMENT.n].typemouvement = typemouvement;
			MOUVEMENT.t[MOUVEMENT.n].unite = unite;
			MOUVEMENT.t[MOUVEMENT.n].unitepass = unitepass;
			MOUVEMENT.t[MOUVEMENT.n].zonedest = zonedest;
			MOUVEMENT.t[MOUVEMENT.n].valable = TRUE;
			MOUVEMENT.t[MOUVEMENT.n].dedaigne = FALSE;
			MOUVEMENT.t[MOUVEMENT.n].paradoxe = FALSE;
			MOUVEMENT.t[MOUVEMENT.n].coupe = FALSE;
			MOUVEMENT.t[MOUVEMENT.n].noligne = noligne;

			assert(++MOUVEMENT.n != NMOUVEMENTS);
			gettoken(fd, &tok); /* Pour faire comme tous les parse : manger la fin de ligne (deja verifie) */
			ordrespays++;
			etat = MOUV0;
			break;

		default:
			assert(FALSE); /* On ne doit pas passer par la */
		}

	}
}

void parseretraites(char *nomfic) {
	FILE *fd;
	TOKEN tok;
	ETATAUTORETR etat;
	char buf[TAILLEMESSAGE], nomunite[2 * TAILLEMOT], nomzone[TAILLEMOT * 2];
	_COTEPOSS *p;
	int nbcotesposs;
	TYPEUNITE typeunite;
	TYPERETRAITE typeretraite;
	_ZONE *zonedest, *zonedest2;
	_DELOGEE *delogee;
	_PAYS *pays, *paysprec;
	int ordrespays;
	BOOL ouverte,zonetrouvee;

	if ((fd = fopen(nomfic, "r")) == NULL) {
		cherchechaine(__FILE__, 170, buf, 1, nomfic); /*"Impossible de lire les ordres de retraite : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	pays = NULL;
	lecture = ORDRES;
	(void) strcpy(image, "");
	changeligne = FALSE;
	noligne = 1;

	etat = RETRINIT;

	typeunite = -1; /* Evite un avertissemnt du compilateur */
	typeretraite = -1; /* Evite un avertissemnt du compilateur */
	zonedest = NULL; /* Evite un avertissemnt du compilateur */
	delogee = NULL; /* Evite un avertissemnt du compilateur */
	ordrespays = -1; /* Evite un avertissemnt du compilateur */

	for (;;) {
		gettoken(fd, &tok);
		switch (etat) {

		case RETRINIT:
			switch (tok.id) {
			case FINLIGNE:
				continue;
			case FINFICHIER:
				cherchechaine(__FILE__, 171, buf, 0); /*"Fichier  sans ordres"*/
				avertir(buf);
				(void) fclose(fd);
				return;
			case CHAINE:
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 172, buf, 1, tok.val); /*"Retraites : pays %1 inconnu"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				ordrespays = 0;
				etat = RETR4;
				break;
			default:
				cherchechaine(__FILE__, 173, buf, 0); /*"Retraites : nom de pays attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case RETR4:
			if (tok.id != FINLIGNE) {
				cherchechaine(__FILE__, 222, buf, 0); /*"Aller a la ligne apres le nom de pays"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			ungettoken(&tok);
			etat = RETR0;
			break;

		case RETR0:
			switch (tok.id) {
			case FINLIGNE:
				continue;
			case FINFICHIER:
				if (ordrespays == 0) {
					cherchechaine(__FILE__, 174, buf, 1, pays->nom); /*"Retraites : pays %1 declare mais sans ordres"*/
					avertir(buf);
				}
				(void) fclose(fd);
				return;
			case UNEARMEESUICIDE:
				typeunite = ARMEE;
				etat = RETR1;
				break;
			case UNEFLOTTE:
				typeunite = FLOTTE;
				etat = RETR1;
				break;
			case CHAINE:
				paysprec = pays;
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 175, buf, 1, tok.val); /*"Pays %1 inconnu ou mauvais debut d'ordre de retraite"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if (paysprec != NULL && ordrespays == 0) {
					cherchechaine(__FILE__, 220, buf, 1, paysprec->nom); /*"Retraites : pays %1 declare mais sans ordres"*/
					avertir(buf);
				}
				ordrespays = 0;
				break;
			case UNERETRAITE:
				cherchechaine(__FILE__, 231, buf, 0); /*"Il est preferable d'utiliser '-' plutot que 'R' pour retirer une unite"*/
				informer(buf);
				cherchechaine(__FILE__, 254, buf, 0); /*"Ce n'est pas une phase d'ajustements"*/
				erreurparse(pays, LASITUATION, FALSE, buf);
				break;
			case UNAJOUT:
			case UNREMOVE:
			case UNEATTAQUESUPPRESSION:
				cherchechaine(__FILE__, 254, buf, 0); /*"Ce n'est pas une phase d'ajustements"*/
				erreurparse(pays, LASITUATION, FALSE, buf);
				break;
			default:
				cherchechaine(__FILE__, 176, buf, 0); /*"Type d'unite 'A' ou 'F' ou nom de pays attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case RETR1:
			if (tok.id != CHAINE) {
				cherchechaine(__FILE__, 177, buf, 0); /*"Zone de l'unite active d'une retraite attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			(void) strcpy(nomzone, tok.val);
			ouverte = FALSE;
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
				cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
				informer(buf);
				ouverte = TRUE;
				break;
			case UNSLASH:
				cherchechaine(__FILE__, 25, buf, 0); /*"Ne pas utiliser de slash '/' pour les c�tes"*/
				informer(buf);
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
				cherchechaine(__FILE__, 178, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
				informer(buf);
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				if (!ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				break;
			default:
				if (ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				ungettoken(&tok);
			}

			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 179, buf, 1, nomzone); /*"Zone %1 inconnue pour unite delogee"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			(void) strcpy(nomunite, pays->nom);
			(void) strcat(nomunite, zonedest->region->nom);
			(void) strcat(nomunite, zonedest->specificite);
			(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));
			if ((delogee = cherchedelogee(nomunite)) == NULL) {
				if (typeunite == FLOTTE && !strcmp(zonedest->specificite, "")
						&& cotesexistent(zonedest)) {
					cherchechaine(__FILE__, 238, buf, 0); /*"Attention : si la province a des cotes, la preciser pour une flotte en unite active ordres retraite"*/
					avertir(buf);
					for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
						(void) strcpy(nomunite, pays->nom);
						(void) strcat(nomunite, zonedest->region->nom);
						(void) strcat(nomunite, p->nom);
						(void) strcat(nomunite, "F");
						if ((delogee = cherchedelogee(nomunite)) != NULL)
							break;
					}
				}
				if (typeunite == ARMEE && strcmp(zonedest->specificite, "")
					&& cotesexistent(zonedest)) {
					cherchechaine(__FILE__, 259, buf, 0); /*"Attention : si la province a des cotes, ne pas la preciser pour une armee "*/
					avertir(buf);
				}
				if (delogee == NULL) {
					cherchechaine(__FILE__, 62, buf, 0); /*"Attention : il s'agit d'une phase de retraites"*/
					avertir(buf);
					if (!compatibles(typeunite, zonedest)) {
						cherchechaine(__FILE__, 248, buf, 0); /*"Une telle unite ne peut se trouver a cet endroit"*/
						erreurparse(pays, LESREGLES, FALSE, buf);
					}
					(void) strcpy(nomunite, pays->nom);
					(void) strcat(nomunite, zonedest->region->nom);
					(void) strcat(nomunite, zonedest->specificite);
					(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));
					cherchechaine(__FILE__, 180, buf, 1, nomunite); /*"Unite delogee %1 inconnue"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}
			}
			etat = RETR2;
			break;

		case RETR2:
			switch (tok.id) {
			case UNEARMEESUICIDE:
				typeretraite = SUICIDE; /* enfin ! */
				etat = RETRFIN;
				break;
			case UNSUICIDE:
				cherchechaine(__FILE__, 227, buf, 0); /*"Utiliser 'a' plutot que 'd' pour une dispersion d'unite"*/
				informer(buf);
				typeretraite = SUICIDE; /* enfin ! */
				etat = RETRFIN;
				break;
			case UNEATTAQUESUPPRESSION:
				cherchechaine(__FILE__, 232, buf, 0); /*"Il est preferable d'utiliser 'R' plutot que '-' pour retraiter une unite"*/
				informer(buf);
				gettoken(fd, &tok);
				if (tok.id == UNOFFTHEBOARD) {
					cherchechaine(__FILE__, 253, buf, 0); /*"Il est preferable d'utiliser 'A' pour disperser une unite"*/
					informer(buf);
					typeretraite = SUICIDE; /* enfin ! */
					etat = RETRFIN;
				} else {
					ungettoken(&tok);
					typeretraite = FUITE; /* enfin ! */
					etat = RETR3;
				}
				break;
			case UNERETRAITE:
				gettoken(fd, &tok);
				if (tok.id == UNOFFTHEBOARD) {
					cherchechaine(__FILE__, 253, buf, 0); /*"Il est preferable d'utiliser 'A' pour disperser une unite"*/
					informer(buf);
					typeretraite = SUICIDE; /* enfin ! */
					etat = RETRFIN;
				} else if(tok.id == UNEATTAQUESUPPRESSION) {
					cherchechaine(__FILE__, 269, buf, 0); /*"Eviter la construction R - "*/
					informer(buf);
					typeretraite = FUITE; /* enfin ! */
					etat = RETR3;
				} else {
					ungettoken(&tok);
					typeretraite = FUITE; /* enfin ! */
					etat = RETR3;
				}
				break;
			case UNSTAND:
			case UNSOUTIEN:
			case UNCONVOI:
				cherchechaine(__FILE__, 229, buf, 0); /*"Il s'agit d'une phase de retraites et non de mouvements"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				break;
			default:
				cherchechaine(__FILE__, 181, buf, 0); /*"Ordre unite en retraite 'R' ou 'A' attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				break;
			}
			break;

		case RETR3:
			switch (tok.id) {
			case FINLIGNE:
			case FINFICHIER:
				cherchechaine(__FILE__, 39, buf, 0); /*"Utiliser 'A' pour une retraite dispersion"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				break;
			case CHAINE:
				break;
			default:
				if(tok.id == UNEARMEESUICIDE) {
					cherchechaine(__FILE__, 15, buf, 0); /*"Ne pas utiliser la construction 'R A'"*/
					avertir(buf);
				}
				cherchechaine(__FILE__, 182, buf, 0); /*"Zone destination retraite attendu"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			(void) strcpy(nomzone, tok.val);
			ouverte = FALSE;
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
				cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
				informer(buf);
				ouverte = TRUE;
				break;
			case UNSLASH:
				cherchechaine(__FILE__, 25, buf, 0); /*"Ne pas utiliser de slash '/' pour les c�tes"*/
				informer(buf);
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
				cherchechaine(__FILE__, 183, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
				informer(buf);
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				if (!ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				break;
			default:
				if (ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				ungettoken(&tok);
			}

			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 184, buf, 1, nomzone); /*"Zone %1 inconnue"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			etat = RETRFIN;
			break;

		case RETRFIN:
			if (tok.id != FINLIGNE && tok.id != FINFICHIER) {
				cherchechaine(__FILE__, 185, buf, 0); /*"El�ments superflus dans un ordre de retraites"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			ungettoken(&tok); /* Se remet sur la bonne ligne */
			switch (typeretraite) {

			case FUITE:
				if (!compatibles(delogee->unite->typeunite, zonedest)) {
					zonetrouvee = FALSE;
					if (delogee->unite->typeunite == FLOTTE && !strcmp(
							zonedest->specificite, "") && cotesexistent(
							zonedest)) {
						cherchechaine(__FILE__, 186, buf, 0); /*"Attention : si la region a des cotes, la preciser pour une flotte lors d'une retraite"*/
						avertir(buf);
						/* On va essayer de trouver la cote quand meme */
						nbcotesposs = 0;
						for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
							(void) strcpy(nomzone, zonedest->region->nom);
							(void) strcat(nomzone, p->nom);
							if (((zonedest2 = cherchezone(nomzone)) != NULL)
									&& compatibles(delogee->unite->typeunite,
											zonedest2) && flottevoisin(
									delogee->unite->zone, zonedest2)) {
								nbcotesposs++;
								zonedest = zonedest2;
							}
						}
						/* Exactement une seule cote possible : l'ambiguite est levee */
						if(nbcotesposs == 1)
							zonetrouvee = TRUE;
					}
					/* Cas de zone parasite pour une armee (pour justifier l'erreur qui va suivre) */
					if (delogee->unite->typeunite == ARMEE && strcmp(
							zonedest->specificite, "")) {
						cherchechaine(__FILE__, 194, buf, 0); /*"Attention : pas de cote pour une armee"*/
						avertir(buf);
					}
					/* On a pas trouve la zone par deduction */
					if (!zonetrouvee) {
						cherchechaine(__FILE__, 187, buf, 0); /*"Incompatibilite de types entre unite fuyarde et zone destination"*/
						erreurparse(pays, LESREGLES, FALSE, buf);
					}
				}
				if (delogee->unite->zone->region == zonedest->region) {
					if (delogee->unite->zone != zonedest) {
						cherchechaine(__FILE__, 244, buf, 0); /*"Attention : on ne peut aller d'une cote � une autre"*/
						informer(buf);
					}
					cherchechaine(__FILE__, 260, buf, 0); /*"L'unite retraitant tente de faire du surplace (!)"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (delogee->unite->typeunite == FLOTTE && !flottevoisin(
						delogee->unite->zone, zonedest)) {
					cherchechaine(__FILE__, 188, buf, 0); /*"La flotte n'a pas acces a la zone"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if (delogee->unite->typeunite == ARMEE && !armeevoisin(
						delogee->unite->zone, zonedest)) {
					cherchechaine(__FILE__, 189, buf, 0); /*"L'armee n'a pas acces a la zone"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if (zonedest->region == delogee->zoneorig->region) {
					cherchechaine(__FILE__, 190, buf, 0); /*"Interdit de retraiter dans la region de l'unite qui deloge"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (chercheoccupant(zonedest->region) != NULL) {
					cherchechaine(__FILE__, 191, buf, 0); /*"Retraite dans une region occupee"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}
				if (interditretraite(zonedest->region)) {
					cherchechaine(__FILE__, 192, buf, 0); /*"Retraite dans une region interdite (bloquee)"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}
				break;

			case SUICIDE:
				break; /* Rien a verifier */
			}
			RETRAITE.t[RETRAITE.n].typeretraite = typeretraite;
			RETRAITE.t[RETRAITE.n].delogee = delogee;
			RETRAITE.t[RETRAITE.n].zonedest = zonedest;
			RETRAITE.t[RETRAITE.n].valable = TRUE;
			RETRAITE.t[RETRAITE.n].noligne = noligne;

			assert(++RETRAITE.n != NRETRAITES);
			gettoken(fd, &tok); /* Pour faire comme tous les parse : manger la fin de ligne (deja verifie) */
			ordrespays++;
			etat = RETR0;
			break;

		default:
			assert(FALSE); /* On ne doit pas passer par la */

		}

	}
}

void parseajustements(char *nomfic) {
	FILE *fd;
	TOKEN tok;
	ETATAUTOAPPR etat;
	char buf[TAILLEMESSAGE], nomunite[2 * TAILLEMOT], nomzone[TAILLEMOT * 2];
	int ordrespays;
	BOOL typeunitefourni, ouverte;
	TYPEUNITE typeunite;
	TYPEAJUSTEMENT typeajustement;
	_CENTREDEPART *centredepart;
	_CENTRE *centre;
	_ZONE *zonedest;
	_UNITE *unite;
	_PAYS *pays, *paysprec;
	_COTEPOSS *p;
	int possessions, unites, possibles, souhaites;

	if ((fd = fopen(nomfic, "r")) == NULL) {
		cherchechaine(__FILE__, 195, buf, 1, nomfic); /*"Impossible de lire les ordres d'ajustements : %1"*/
		erreur(NULL, ERRSYSTEME, buf);
	}

	pays = NULL;
	lecture = ORDRES;
	(void) strcpy(image, "");
	changeligne = FALSE;
	noligne = 1;

	etat = APPRINIT;

	typeunite = -1; /* Evite un avertissemnt du compilateur */
	typeajustement = -1; /* Evite un avertissemnt du compilateur */
	zonedest = NULL; /* Evite un avertissemnt du compilateur */
	ordrespays = -1; /* Evite un avertissemnt du compilateur */
	unite = NULL; /* Evite un avertissemnt du compilateur */
	typeunitefourni = FALSE; /* Evite un avertissemnt du compilateur */

	for (;;) {
		gettoken(fd, &tok);
		switch (etat) {

		case APPRINIT:
			switch (tok.id) {
			case FINLIGNE:
				continue;
			case FINFICHIER:
				cherchechaine(__FILE__, 196, buf, 0); /*"Ajustements : fichier sans ordres"*/
				avertir(buf);
				(void) fclose(fd);
				return;
			case CHAINE:
				if ((pays = cherchepays(tok.val)) == NULL) {
					cherchechaine(__FILE__, 197, buf, 1, tok.val); /*"Ajustements : pays %1 inconnu"*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				ordrespays = 0;
				etat = APPR3;
				break;
			default:
				cherchechaine(__FILE__, 198, buf, 0); /*"Ajustements : nom de pays attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case APPR3:
			if (tok.id != FINLIGNE) {
				cherchechaine(__FILE__, 221, buf, 0); /*"Aller a la ligne apres le nom de pays"*/
				erreurparse(pays, SYNTAXIQUE, FALSE, buf);
			}
			etat = APPR0;
			ungettoken(&tok);
			break;

		case APPR0:
			switch (tok.id) {
			case FINLIGNE:
				continue;
			case FINFICHIER:
				if (ordrespays == 0) {
					cherchechaine(__FILE__, 199, buf, 1, pays->nom); /*"Ajustements : pays %1 declare mais sans ordres"*/
					avertir(buf);
				}
				(void) fclose(fd);
				return;
			case UNAJOUT:
				typeajustement = AJOUTE;
				etat = APPR1;
				break;
			case UNERETRAITE:
				cherchechaine(__FILE__, 231, buf, 0); /*"Il est preferable d'utiliser '-' plutot que 'R' pour retirer une unite"*/
				informer(buf);
				typeajustement = SUPPRIME;
				etat = APPR1;
				break;
			case UNREMOVE:
				typeajustement = SUPPRIME;
				etat = APPR1;
				break;
			case UNEATTAQUESUPPRESSION:
				typeajustement = SUPPRIME;
				etat = APPR1;
				break;
			case CHAINE:
				paysprec = pays;
				if ((pays = cherchepays(tok.val)) != NULL) {
					if (paysprec != NULL && ordrespays == 0) {
						cherchechaine(__FILE__, 200, buf, 1, paysprec->nom); /*"Ajustements : pays %1 declare mais sans ordres"*/
						avertir(buf);
					}
					ordrespays = 0;
				} else {
					/* Autorise une ellipse : directement le trigramme, pas de '+', pas de 'A',  */
					ungettoken(&tok); /* on va essayer de se passer du type d'unite */
					lesajustements(pays, &possessions, &unites, &possibles);
					souhaites = INF(possessions - unites, possibles);
					cherchechaine(__FILE__, 202, buf, 0); /*"Il est preferable de mettre un '+' ou '-'"*/
					avertir(buf);
					if (souhaites >= 0) {
						cherchechaine(__FILE__, 255, buf, 0); /*"Construction presumee"*/
						informer(buf);
						typeajustement = AJOUTE;
					} else {
						cherchechaine(__FILE__, 256, buf, 0); /*"Suppression presumee"*/
						informer(buf);
						typeajustement = SUPPRIME;
					}
					typeunitefourni = FALSE;
					etat = APPR2;
				}
				break;
			case UNEARMEESUICIDE:
			case UNEFLOTTE:
				/* Autorise une ellipse : pas de '+' ni '-' */
				cherchechaine(__FILE__, 202, buf, 0); /*"Il est preferable de mettre un '+' ou '-'"*/
				avertir(buf);
				ungettoken(&tok);
				lesajustements(pays, &possessions, &unites, &possibles);
				souhaites = INF(possessions - unites, possibles);
				if (souhaites >= 0) {
					cherchechaine(__FILE__, 255, buf, 0); /*"Construction presumee"*/
					informer(buf);
					typeajustement = AJOUTE;
				} else {
					cherchechaine(__FILE__, 256, buf, 0); /*"Construction presumee"*/
					informer(buf);
					typeajustement = SUPPRIME;
				}
				typeunitefourni = TRUE;
				etat = APPR1;
				break;
			default:
				cherchechaine(__FILE__, 252, buf, 0); /*"Attention : il s'agit d'une phase d'ajustements"*/
				avertir(buf);
				cherchechaine(__FILE__, 203, buf, 0); /*"Type d'ajustement ('-' ou '+') ou nom de pays attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case APPR1:
			switch (tok.id) {
			case UNEARMEESUICIDE:
				typeunite = ARMEE;
				typeunitefourni = TRUE;
				etat = APPR2;
				break;
			case UNEFLOTTE:
				typeunite = FLOTTE;
				typeunitefourni = TRUE;
				etat = APPR2;
				break;
			case CHAINE:
				typeunitefourni = FALSE;
				ungettoken(&tok); /* on va essayer de se passer du type d'unite */
				etat = APPR2;
				break;
			default:
				cherchechaine(__FILE__, 207, buf, 0); /*"Type d'unite 'A' ou 'F' attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			break;

		case APPR2:
			if (tok.id != CHAINE) {
				cherchechaine(__FILE__, 208, buf, 0); /*"Zone de l'unite attendu"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
			}
			(void) strcpy(nomzone, tok.val);
			ouverte = FALSE;
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEOUVRANTE:
				cherchechaine(__FILE__, 11, buf, 0); /*"Ne pas utiliser de parenth�se pour les c�tes"*/
				informer(buf);
				ouverte = TRUE;
				break;
			case UNSLASH:
				cherchechaine(__FILE__, 25, buf, 0); /*"Ne pas utiliser de slash '/' pour les c�tes"*/
				informer(buf);
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
				cherchechaine(__FILE__, 209, buf, 0); /*"Il est preferable d'accoller la cote a la region"*/
				informer(buf);
				(void) strcat(nomzone, tok.val);
				break;
			default:
				ungettoken(&tok);
			}
			gettoken(fd, &tok);
			switch (tok.id) {
			case UNEFERMANTE:
				if (!ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				break;
			default:
				if (ouverte) {
					cherchechaine(__FILE__, 47, buf, 0); /*"Probleme de parentheses"*/
					erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				}
				ungettoken(&tok);
			}
			if ((zonedest = cherchezone(nomzone)) == NULL) {
				cherchechaine(__FILE__, 210, buf, 1, nomzone); /*"Zone %1 inconnue pour suppression ou construction"*/
				erreurparse(pays, LACARTE, FALSE, buf);
			}

			if (typeunitefourni) {

				if (!compatibles(typeunite, zonedest)) {
					switch (typeajustement) {
					case AJOUTE:
						if (typeunite == FLOTTE && cotesexistent(zonedest)) {
							cherchechaine(__FILE__, 239, buf, 0); /*"Attention : si la province a des cotes, la preciser pour une flotte a ajouter ou supprimer"*/
							avertir(buf);
						}
						if (typeunite == ARMEE && cotesexistent(zonedest)) {
							cherchechaine(__FILE__, 194, buf, 0); /*"Attention : pas de cote pour une armee"*/
							avertir(buf);
						}
						cherchechaine(__FILE__, 201, buf, 0); /*"L'unite a ajouter n'est pas du type de celles qui peuvent etre placees sur la  province (ou zone dans une province)" d'apr�s le type fourni */
						erreurparse(pays, LESREGLES, FALSE, buf);
						break;
					case SUPPRIME:
						unite = NULL;
						if (typeunite == FLOTTE && cotesexistent(zonedest)) {
							for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
								(void) strcpy(nomunite, zonedest->region->nom);
								(void) strcat(nomunite, p->nom);
								(void) strcat(nomunite, "F");
								if ((unite = chercheunite(nomunite)) != NULL)
									break;
							}
						}
						if (typeunite == ARMEE && cotesexistent(zonedest)) {
							cherchechaine(__FILE__, 194, buf, 0); /*"Attention : pas de cote pour une armee"*/
							avertir(buf);
						}
						if (unite == NULL) {
							cherchechaine(__FILE__, 205, buf, 0); /*"L'unite a retirer n'est pas du type de celles qui peuvent etre placees sur la  province (ou zone dans une province)"*/
							erreurparse(pays, LESREGLES, FALSE, buf);
						}
						break;
					}
				}

			} else { /* Type unite non fourni */

				switch (typeajustement) { /* On va deviner le type de l'unite */

				case SUPPRIME: /* D'apr�s ce qu'on trouve � cet endroit */
					/* Pas de message d'erreur � ce niveau, on verra plus tard,
					 on se contente de trouver le type d'unite le plus plausible */
					switch (zonedest->typezone) {
					case TERRE:
						typeunite = ARMEE;
						break;
					case MER:
						typeunite = FLOTTE;
						break;
					case COTE:
						if (strcmp(zonedest->specificite, ""))
							typeunite = FLOTTE;
						else {
							/* Trouve -t- on une flotte ? */
							typeunite = FLOTTE;
							(void) strcpy(nomunite, zonedest->region->nom);
							(void) strcat(nomunite, zonedest->specificite);
							(void) strcat(nomunite, (typeunite == ARMEE ? "A"
									: "F"));
							if ((unite = chercheunite(nomunite)) == NULL) {
								/* Trouve -t- on une flotte sur une cote ? */
								if (cotesexistent(zonedest)) {
									for (p = COTEPOSS.t; p < COTEPOSS.t
											+ COTEPOSS.n; p++) {
										(void) strcpy(nomunite,
												zonedest->region->nom);
										(void) strcat(nomunite, p->nom);
										(void) strcat(nomunite, "F");
										if ((unite = chercheunite(nomunite))
												!= NULL)
											break;
									}
								}
							}
							/* Sinon une armee, on verra bien... */
							if (unite == NULL)
								typeunite = ARMEE;
						}
						break;
					} /* switch typezone */
					break;

				case AJOUTE: /* D'apr�s ce qu'on peut mettre � cet endroit */
					cherchechaine(__FILE__, 245, buf, 0); /*"Attention : il faut pr�ciser le type de l'unit� � construire"*/
					avertir(buf);
					switch (zonedest->typezone) {
					case TERRE:
						typeunite = ARMEE;
						break;
					case MER:
						cherchechaine(__FILE__, 193, buf, 0); /*"On ne peut pas construire en mer"*/
					erreurparse(pays, SYNTAXIQUE, FALSE, buf);
						break;
					case COTE: /* cote */
						if (strcmp(zonedest->specificite, ""))
							typeunite = FLOTTE;
						else {
							if (cotesexistent(zonedest)) {
								cherchechaine(__FILE__, 239, buf, 0); /*"Attention : si la province a des cotes, la preciser pour une flotte a ajouter ou supprimer"*/
								avertir(buf);
							}
							cherchechaine(__FILE__, 204, buf, 0); /*"Ambiguite sur le type d'unite"*/
							erreurparse(pays, SYNTAXIQUE, FALSE, buf);
						}
						break;
					} /* switch typezone */
				} /* switch typeajustement */
			} /* if */
			etat = APPRFIN;
			break;

		case APPRFIN:
			switch (tok.id) {
			case FINLIGNE:
			case FINFICHIER:
				break;
			case UNEATTAQUESUPPRESSION:
			case UNSOUTIEN:
			case UNSTAND:
			case UNCONVOI:
			case UNERETRAITE:
			case UNEARMEESUICIDE:
				cherchechaine(__FILE__, 252, buf, 0); /*"Attention : il s'agit d'une phase d'ajustements"*/
				avertir(buf);
				/* Fall through */
			default:
				cherchechaine(__FILE__, 211, buf, 0); /*"El�ments superflus dans un ordre d'ajustements"*/
				erreurparse(pays, SYNTAXIQUE, tok.id == FINLIGNE, buf);
				break;
			}
			ungettoken(&tok); /* Se remet sur la bonne ligne */
			switch (typeajustement) {

			case SUPPRIME:
				(void) strcpy(nomunite, zonedest->region->nom);
				(void) strcat(nomunite, zonedest->specificite);
				(void) strcat(nomunite, (typeunite == ARMEE ? "A" : "F"));
				if ((unite = chercheunite(nomunite)) == NULL) {
					if (typeunite == FLOTTE && !strcmp(zonedest->specificite,
							"") && cotesexistent(zonedest)) {
						cherchechaine(__FILE__, 246, buf, 0); /*"Attention : si la province a des cotes, la preciser pour une flotte a supprimer"*/
						avertir(buf);
						for (p = COTEPOSS.t; p < COTEPOSS.t + COTEPOSS.n; p++) {
							(void) strcpy(nomunite, zonedest->region->nom);
							(void) strcat(nomunite, p->nom);
							(void) strcat(nomunite, "F");
							if ((unite = chercheunite(nomunite)) != NULL)
								break;
						}
					}
					if (unite == NULL) {
						cherchechaine(__FILE__, 212, buf, 1, nomunite); /*"Unite %1 a supprimer inconnue"*/
						erreurparse(pays, LASITUATION, FALSE, buf);
					}
				}
				if (unite->pays != pays) {
					cherchechaine(__FILE__, 213, buf, 1, nomunite); /*"Unite %1 a supprimer pas du pays du donneur d'ordres"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}
				break;

			case AJOUTE:
				if ((centre = cherchecentre(zonedest->region->nom)) == NULL) {
					cherchechaine(__FILE__, 251, buf, 1, zonedest->region->nom); /*"R�gion %1 pas centre "*/
					erreurparse(pays, LACARTE, FALSE, buf);
				}
				if(!OPTIONE) {
					/* Standard rules : we worry about the center being a start center */
					if ((centredepart = cherchecentredepart(zonedest->region->nom))
							== NULL) {
						cherchechaine(__FILE__, 214, buf, 1, zonedest->region->nom); /*"Centre %1 pas centre de depart"*/
						erreurparse(pays, LACARTE, FALSE, buf);
					}
					if (centredepart->pays != pays) {
						cherchechaine(__FILE__, 215, buf, 0); /*"Pas centre de depart du bon pays"*/
						erreurparse(pays, LACARTE, FALSE, buf);
					}
				}
				if (!possede(pays, centre)) {
					cherchechaine(__FILE__, 216, buf, 0); /*"Le pays ne possede pas le centre"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}
				if (!compatibles(typeunite, zonedest)) {
					if (typeunite == FLOTTE && !strcmp(zonedest->specificite,
							"") && cotesexistent(zonedest)) {
						cherchechaine(__FILE__, 217, buf, 0); /*"Attention : si la region a des cotes, la preciser pour une flotte lors d'une construction"*/
						avertir(buf);
					}
					if (typeunite == ARMEE && strcmp(zonedest->specificite, "")) {
						cherchechaine(__FILE__, 194, buf, 0); /*"Attention : pas de cote pour une armee"*/
						avertir(buf);
					}
					cherchechaine(__FILE__, 218, buf, 0); /*"Incompatibilite de types entre unite a ajouter et sa zone"*/
					erreurparse(pays, LESREGLES, FALSE, buf);
				}
				if (chercheoccupant(zonedest->region) != NULL) {
					cherchechaine(__FILE__, 219, buf, 0); /*"Il y a deja une unite a cet endroit"*/
					erreurparse(pays, LASITUATION, FALSE, buf);
				}

				UNITEFUTURE.t[UNITEFUTURE.n].pays = pays;
				UNITEFUTURE.t[UNITEFUTURE.n].typeunite = typeunite;
				UNITEFUTURE.t[UNITEFUTURE.n].zone = zonedest;
				UNITEFUTURE.t[UNITEFUTURE.n].zonedepart = zonedest;
				unite = UNITEFUTURE.t + UNITEFUTURE.n;
				assert(++UNITEFUTURE.n != NUNITEFUTURES);
				break;
			} /* switch typeajustement */

			AJUSTEMENT.t[AJUSTEMENT.n].typeajustement = typeajustement;
			AJUSTEMENT.t[AJUSTEMENT.n].unite = unite;
			AJUSTEMENT.t[AJUSTEMENT.n].noligne = noligne;

			assert(++AJUSTEMENT.n != NAJUSTEMENTS);
			gettoken(fd, &tok); /* Pour faire comme tous les parse : manger la fin de ligne (deja verifie) */
			ordrespays++;
			etat = APPR0;
			break;

		default:
			assert(FALSE); /* On ne doit pas passer par la */

		} /* switch (etat) */

	} /* for(;;); */
}
