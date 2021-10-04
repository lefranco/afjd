#include <sys/types.h>

#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include <wchar.h>
#include <stdlib.h>
#include <time.h>

/* #define TESTUNITAIRE */
/* #define DEBUG */
/* #define DEBUG_SIMIL*/

/* Des prototypes qui semblent manquer */
int strcasecmp(const char *, const char *);
#ifdef TESTUNITAIRE
long lrand48(void);
void srand48(long);
#endif

#define EOS '\0'

#define NBMAXMOTS 30
#define SIZEMAXMOT 255
#define SIZEMAXLIGNE 1024

#define INF(x,y) ((x) < (y) ? (x) : (y))
#define SUP(x,y) ((x) > (y) ? (x) : (y))

#define SQR(x) ((x) * (x))

#define SEUIL 75
#define SEUILSUR 99

#ifdef TESTUNITAIRE
#define NBTESTS 10000
#endif

typedef enum {
	FALSE = 0, TRUE
} BOOL;

typedef struct _listeconf { /* conflits */
	char *val;
	char *valref;
	struct _listeconf *suiv;
} LISTECONF;

typedef struct { /* rapport de comparaison */
	int similitude;
	char *modele;
	LISTECONF *conflits;
} MATCH;

typedef struct { /* rapport de comparaison */
	MATCH match;
	int lon;
	BOOL conv;
	char buf[100];
} ELEMENT;

typedef struct _listesyn { /* synonymes */
	char *val;
	struct _listesyn *suiv;
} LISTESYN;

typedef struct _dico { /* dictionnaire */
	char *ref;
	char *synoff;
	struct _listesyn *lsyn;
	struct _dico *suiv;
} DICO;

/* On ne prend en compte que le clavier americain */
static char KEYBOARD[3][10] = {
	{ 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P' },
	{ 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ' ' },
	{ ' ', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ' ', ' ' },
};

static char KEYS[26] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

/* Globale : le dictionnaire */
static DICO *dictionnaire;

/* racine carree entier */
static int racinecarree(const int x) {
	int n;

	/* Protection */
	if(x < 0)
		return 0;

	n = 0;
	while(SQR(n) <= x)
		n++;

	return n-1;
}

/* Renvoie vrai si les deux lettres sont voisines sur le clavier americain */
static BOOL voisinsclavier(const char c1, const char c2) {

	int i, j, posx1, posy1, posx2, posy2, dist;
	char uc1, uc2;

	if (c1 == EOS || c2 == EOS) {
		(void) fprintf(stderr, "Erreur interne : Pb voisinclavier()\n");
		exit(-1);
	}

	uc1 = (char) toupper((int)c1);
	uc2 = (char) toupper((int)c2);

	if (!strchr(KEYS, uc1))
		return FALSE;
	if (!strchr(KEYS, uc2))
		return FALSE;

	posx1 = posy1 = posx2 = posy2 = -1;

	for (i = 0; i < 10; i++)
		for (j = 0; j < 3; j++)
			if (KEYBOARD[j][i] == uc1) {
				posx1 = i;
				posy1 = j;
				i = 10; /* sortie des deux boucles */
				break;
			}

	/* si on a pas trouve le premier caractere */
	if (posx1 == -1 || posy1 == -1)
		return FALSE;

	for (i = 0; i < 10; i++)
		for (j = 0; j < 3; j++)
			if (KEYBOARD[j][i] == uc2) {
				posx2 = i;
				posy2 = j;
				i = 10; /* sortie des deux boucles */
				break;
			}

	/* si on a pas trouve le deuxieme caractere */
	if (posx2 == -1 || posy2 == -1)
		return FALSE;

	dist = SQR(posx1-posx2) + SQR(posy1-posy2);

/*
 #ifdef DEBUG
	 (void) printf("d(%c,%c) ->%d\n",c1,c2,dist);
 #endif
 */

	return dist <= 2;
}

/* Renvoie (en pourcentage) la similitude entre les deux chaines passees en argment */
static int similitude(const char *s1, const char *s2) {

	char buf1[SIZEMAXMOT], buf2[SIZEMAXMOT], *p;
	int pos1, pos2, delta, maxdelta, d1, d2, mil, dmil, mdmil, sig;
	int differents, proches, egaux, n;
	BOOL matchsuivant;

	if (strlen(s1) > SIZEMAXMOT - 1) {
		(void) fprintf(stderr, "Erreur interne : Pb %s\n",s1);
		exit(-1);
	}
	if (strlen(s2) > SIZEMAXMOT - 1) {
		(void) fprintf(stderr, "Erreur interne : Pb %s\n", s2);
		exit(-1);
	}

	/* On met la plus petite chaine en premier */
	if (strlen(s1) < strlen(s2)) {
		(void) strcpy(buf1, s1);
		(void) strcpy(buf2, s2);
	} else {
		(void) strcpy(buf2, s1);
		(void) strcpy(buf1, s2);
	}

	/* On met tout en majuscules */
	for (p = buf1; *p; p++)
		*p = (char) toupper((int) *p);

	for (p = buf2; *p; p++)
		*p = (char) toupper((int) *p);

	proches = differents = egaux = 0;
	pos1 = pos2 = 0;

	for (;;) {

		/* progression normale */
		while ((unsigned) pos1 < strlen(buf1) && (unsigned) pos2 < strlen(buf2)
				&& buf1[pos1] == buf2[pos2]) {
			pos1++;
			pos2++;
			egaux++;
		}

		/* different, recherche match suivant */
		matchsuivant = FALSE;
		maxdelta = INF(strlen(buf1) - pos1,strlen(buf2) - pos2);
		for (delta = 1; delta <= maxdelta; delta++) {

			/* On ordonne les ecarts pour commencer par les plus voisins du milieu */
			mil = mdmil = delta / 2;
			if (delta % 2 == 1)
				mdmil++;
			for (dmil = 0; dmil <= mdmil; dmil++)
				for (sig = 1; sig >= -1; sig -= 2) {
					d1 = mil + dmil * sig;
					d2 = delta - d1;
					if (d1 < 0 || d2 < 0)
						continue;

					/* Si match plus loin */
					if (buf1[pos1 + d1] == buf2[pos2 + d2]) {

						/* attenuation differences proches sur le clavier */
						if (d1 == 1 && d2 == 1 &&
							voisinsclavier(buf1[pos1],buf2[pos2]))
							proches++;

						pos1 += d1;
						pos2 += d2;

						n = 100 * SUP(d1,d2);/* Gain en precision : on gere 100 fois la valeur */
						differents += SQR(n);

						delta = maxdelta + 1; /* sortie deuxieme boucle */
						dmil = mdmil + 1; /* sortie troisieme boucle */
						matchsuivant = TRUE;
						break; /* sortir boucles */

					} /* match plus loin */

				} /* boucle d1 */
		} /* boucle delta*/

		if (matchsuivant)
			continue;

		/* Ici c'est qu'on a fini de comparer */
		n = 100 * SUP((strlen(buf1) - pos1),(strlen(buf2) - pos2));	  /* Gain en precision : on gere 100 fois la valeur */
 		differents += SQR(n);

		/* Gain en precision : on gere 100 fois la valeur */
		proches *= 100;
		egaux *= 100;

		/* Heuristique : les caracteres proches sont comptes comme a moitie differents */
		/* Sous forme de bonus sur le nombre de caracteres egaux */
		egaux += proches/2;

		/* On a fait la somme les carres des differences */
 		differents = racinecarree(differents);

#ifdef DEBUG_SIMIL
 		printf("%s / %s : egaux=%d differents=%d proches=%d\n",s1,s2,egaux,differents,proches);
#endif

		/* On va ramener a un pourcentage */
		return (100 * egaux) / (egaux + differents);

	} /* fin de la boucle infinie */

}

/* Renvoie la meme lettre mais sans l'accent */
static char enleveaccent(const char c) {

	switch (c) {

	/* variantes de 'a' */
	case 'à':
	case 'â':
	case 'ä':
		return 'a';

	/* variantes de 'e' */
	case 'é':
	case 'è':
	case 'ê':
	case 'ë':
		return 'e';

	/* variantes de 'i' */
	case 'î':
	case 'ï':
		return 'i';

	/* variantes de 'o' */
	case 'ô':
	case 'ö':
		return 'o';
		return 'u';

	/* variantes de 'u' */
	case 'ù':
	case 'û':
	case 'ü':
		return 'u';

	/* bonus */
	case 'ç':
		return 'c';

	default:
		return c;

	}
}

/* Lit un mot dans le fichier d'entrée.
 ATTENTION : Tout caractère non alphanumérique est renvoyé individuellement */
static void litmot(FILE *fd, char *mot, BOOL *finligne, BOOL *finfichier) {

	int c;
	int lon;
	char *p;

	/* On passe les espaces */
	for (;;) {
		c = fgetc(fd);
		if (c != ' ' && c != '\t') {
			(void) ungetc(c, fd);
			break;
		}
	}

	/* On voit ce qu'on trouve en premier */
	c = fgetc(fd);

	/* Fin de fichier : c'est fini ! */
	if (c == EOF) {
		*finfichier = TRUE;
		return;
	}
	*finfichier = FALSE;

	/* On passe les commentaires */
	if(c == ';') {
		do {
			c = fgetc(fd);
		} while (!(c == '\n' || c == 13));
	}

	/* Fin de ligne : c'est fini ! */
	if (c == '\n' || c == 13 /* Pour unix */) {

		/* c == 13 ajouté pour unix */
		do {
			c = fgetc(fd);
		} while (c == '\n' || c == 13);
		(void) ungetc(c, fd);

		*finligne = TRUE;
		return;
	}
	*finligne = FALSE;

	/* pointeur ou on va ranger le mot */
	p = mot;

	/* caractere special = mot  avec un seul caractere */
	if (!isalpha(c) && !isdigit(c)) {
		*p++ = (char) c;
		*p = EOS;
		return;
	}

	/* on remet dans le flux car on va lire un mot complet  */
	(void) ungetc(c, fd);

	/* On assemble le mot (il y a au moins une lettre interessante */
	lon = 0;
	for (;;) {

		c = fgetc(fd);

		/* simplifie le probleme en enlevant les accents */
		c = enleveaccent((char) c);

		/* caractere special : fin du mot (sans ce caractere) */
		if (!isalpha(c) && !isdigit(c)) {
			(void) ungetc(c, fd);
			break;
		}

		/* insere la lettre dans le mot */
		*p++ = (char) c;
		lon++;

		/* verification */
		if (lon == SIZEMAXMOT - 1) {
			(void) fprintf(stderr, "Erreur : entree : Mot trop long\n");
			exit(-1);
		}

	}

	/* finit le mot proprement */
	*p = EOS;

}

/* Transforme un '_' en ' ' */
static void souligne2espace(char *s) {
	char *p;

	for (p = s; *p; p++)
		if (*p == '_')
			*p = ' ';
}

/* Libere la memoire d'un conflit */
static void libereconflits(LISTECONF *conflits) {

	LISTECONF *p = conflits, *psuiv;

	for (;;) {
		if (p == NULL)
			break;
		psuiv = p->suiv;
		free(p);
		p = psuiv;
	}
}

/* Scanne le dictionnaire...
 Renvoie VRAI si une référence a été trouvée */
static BOOL convertitmot(const char *mot, char *synoff, MATCH *match) {

	DICO *p;
	LISTESYN *q;
	char *synoffrec = NULL, *synrec = NULL;
	int simil, rang, rangmax;
	LISTECONF *r;
	int similrec = 0, rangrec = -1;

	/* Recherche dans les synonymes */
	for (p = dictionnaire; p; p = p->suiv) {

		/* calcul du rang max */
		rangmax = 0;
		for (q = p->lsyn; q; q = q->suiv)
			rangmax++;

		rang = 1;
		for (q = p->lsyn; q; q = q->suiv) {
			simil = similitude(q->val, mot);

			/* On va privilegier les synonymes en mis en premier */
			if (simil > similrec ||
			   (simil == similrec && (rangmax - rang)< rangrec)) {
				synrec = q->val;
				synoffrec = p->synoff;
				similrec = simil;
				rangrec = rangmax - rang;
			}
			rang++;
		}
	}

#ifdef DEBUG
	(void) printf("%s = %s --> %s %d (%d%%)\n",mot,(!synrec?"":synrec),(!synoffrec?"":synoffrec),rangrec,similrec);
#endif

	/* Initialisations utiles si retour premature dans les lignes ci-dessous */
	(void) strcpy(synoff, "<?>");
	match->conflits = NULL;
	match->similitude = -100;
	match->modele = NULL;

	if (synoffrec == NULL)
		return FALSE;

	if (similrec < SEUIL)
		return FALSE;

	(void) strcpy(synoff, synoffrec);
	souligne2espace(synoff);

	match->similitude = similrec;
	match->modele = synrec;

	/* Recherche les conflits */
	for (p = dictionnaire; p; p = p->suiv) {

		if (!strcmp(p->synoff, synoffrec))
			continue;

		for (q = p->lsyn; q; q = q->suiv) {

			if (!strcmp(q->val, synrec))
				continue;

			simil = similitude(q->val, mot);
			if (simil == similrec) {
				r = (LISTECONF *) malloc(sizeof(LISTECONF));
				r->val = q->val;
				r->valref = p->synoff;
				r->suiv = match->conflits;
				match->conflits = r;
			}
		}
	}

	return TRUE;
}

/* Décide de quelle manière résoudre le conflit "shift reduce"
 Doit on prendre le prochain element seul, le composer avec le suivant, avec les deux suivants etc... */
static int shiftreduce(const ELEMENT elem1, const ELEMENT elem2, const ELEMENT elem3, const ELEMENT elem4, const ELEMENT elem5) {

	int qual1, qual2, qual3, qual4, qual5;

	/* On privilegie plutot d'en prendre le plus possible a partir de trois */
	qual1 = (elem1.conv ? (elem1.match.similitude - SEUIL + 1) * (elem1.match.similitude > SEUILSUR && elem1.lon <= 2 ? 1000 : racinecarree(elem1.lon*10)) : 0);
	qual2 = (elem2.conv ? (elem2.match.similitude - SEUIL + 1) * (elem2.match.similitude > SEUILSUR && elem2.lon <= 2 ? 1000 : racinecarree(elem2.lon*10)) : 0);
	qual3 = (elem3.conv ? (elem3.match.similitude - SEUIL + 1) * (elem3.match.similitude > SEUILSUR && elem3.lon <= 2 ? 1000 : racinecarree(elem3.lon*10)) : 0);
	qual4 = (elem4.conv ? (elem4.match.similitude - SEUIL + 1) * (elem4.match.similitude > SEUILSUR && elem4.lon <= 2 ? 1000 : racinecarree(elem4.lon*10)) : 0);
	qual5 = (elem5.conv ? (elem5.match.similitude - SEUIL + 1) * (elem5.match.similitude > SEUILSUR && elem5.lon <= 2 ? 1000 : racinecarree(elem5.lon*10)) : 0);

#ifdef DEBUG
	(void) printf("shiftreduce %s (conv=%s lon=%d : match.sim=%d qual=%d) \n",
			elem1.buf, elem1.conv?"oui":"non",elem1.lon,(elem1.conv?elem1.match.similitude - SEUIL + 1:-1),qual1);
	(void) printf("shiftreduce %s (conv=%s lon=%d : match.sim=%d qual=%d) \n",
			elem2.buf, elem2.conv?"oui":"non",elem2.lon,(elem2.conv?elem2.match.similitude - SEUIL + 1:-1),qual2);
	(void) printf("shiftreduce %s (conv=%s lon=%d : match.sim=%d qual=%d) \n",
			elem3.buf, elem3.conv?"oui":"non",elem3.lon,(elem3.conv?elem3.match.similitude - SEUIL + 1:-1),qual3);
	(void) printf("shiftreduce %s (conv=%s lon=%d : match.sim=%d qual=%d) \n",
			elem4.buf, elem4.conv?"oui":"non",elem4.lon,(elem4.conv?elem4.match.similitude - SEUIL + 1:-1),qual4);
	(void) printf("shiftreduce %s (conv=%s lon=%d : match.sim=%d qual=%d) \n",
			elem5.buf, elem5.conv?"oui":"non",elem5.lon,(elem5.conv?elem5.match.similitude - SEUIL + 1:-1),qual5);
#endif

	/* Qual 5 est le meilleur */
	if (qual5 > qual1 && qual5 > qual2 && qual5 > qual3 && qual5 > qual4)
		return 5;

	/* Qual 4 est le meilleur */
	if (qual4 > qual1 && qual4 > qual2 && qual4 > qual3)
		return 4;

	/* Qual 3 est le meilleur */
	if (qual3 > qual1 && qual3 > qual2)
		return 3;

	/* Qual 2 est le meilleur */
	if (qual2 > qual1)
		return 2;

	/* Qual 1 est le meilleur */
	return 1;
}

/* Affiche le mot sur la sortie */
static void sortmot(FILE *fd, const char *mot, const BOOL reconnu, LISTECONF *conflits,	BOOL *debutligne) {

	LISTECONF *p;

	if (!strcmp(mot, ""))
		return;

	if (!(*debutligne))
		(void) fprintf(fd, " ");

	if (reconnu) {
		(void) fprintf(fd, "%s", mot);
		if (conflits) {
			/* on a fait un choix mais on aurait pu en faire un autre */
			for (p = conflits; p; p = p->suiv)
				(void) fprintf(fd, " [?=%s]", p->valref);
		}
	} else
		/* on a pas reconnu le truc */
		(void) fprintf(fd, "[??%s]", mot);

	*debutligne = FALSE;
}

/* Traduit une ligne du fichier en entrée */
static void traduitligne(FILE *fd1, FILE *fd2, BOOL *finfichier) {

	char mot[NBMAXMOTS][SIZEMAXMOT];
	char synoff1[SIZEMAXMOT];
	char synoff2[SIZEMAXMOT], synoff21[SIZEMAXMOT], synoff22[SIZEMAXMOT];
	char synoff3[SIZEMAXMOT], synoff31[SIZEMAXMOT], synoff32[SIZEMAXMOT],
			synoff33[SIZEMAXMOT], synoff34[SIZEMAXMOT];
	char synoff4[SIZEMAXMOT];
	char synoff5[SIZEMAXMOT];
	char buffer[30 * SIZEMAXMOT];
	int idmot, nbmots, sel;
	BOOL finligne, debutligne;
	ELEMENT *pelem1, *pelem2, *pelem3, *pelem4, *pelem5;
	ELEMENT elem11, elem21, elem22, elem31, elem32, elem33, elem34, elem41,
			elem51;

	/* On récupère les mots de la ligne */
	idmot = nbmots = 0;
	for (;;) {

		litmot(fd1, mot[idmot++], &finligne, finfichier);

		if (*finfichier || finligne)
			break;

		nbmots++;
		if (nbmots == NBMAXMOTS)
			break;

	}

	/* On va regarder ce qu'on arrive à comprendre dans ce fatras !*/
	idmot = 0;
	debutligne = TRUE;
	for (;;) {

		if (idmot == nbmots)
			return;

		/* Mot reconnu */

		strcpy(elem11.buf,"");
		strcpy(elem21.buf,"");
		strcpy(elem22.buf,"");
		strcpy(elem31.buf,"");
		strcpy(elem32.buf,"");
		strcpy(elem33.buf,"");
		strcpy(elem34.buf,"");
		strcpy(elem41.buf,"");
		strcpy(elem51.buf,"");

		elem11.match.similitude = 0; /* Evite un avertissement */
		elem11.match.modele = NULL;
		elem11.match.conflits = NULL;
		elem11.lon = strlen(mot[idmot]);
		(void) sprintf(buffer, "%s",
			mot[idmot]);
		elem11.conv = convertitmot(buffer, synoff1, &elem11.match);
		strcpy(elem11.buf,buffer);
		pelem1 = &elem11;

		/* On tente avec le suivant */
		elem21.conv = FALSE;
		elem21.match.similitude = 0; /* Evite un avertissement */
		elem21.match.modele = NULL;
		elem21.match.conflits = NULL;
		elem21.lon = 0; /* Evite un avertissement */
		strcpy(elem21.buf,buffer);
		pelem2 = &elem21;

		if (idmot + 1 < nbmots) {

			/* Espaces */
			(void) sprintf(buffer, "%s_%s",
				mot[idmot], mot[idmot + 1]);
			elem21.conv = convertitmot(buffer, synoff21, &elem21.match);
			strcpy(elem21.buf,buffer);
			/* elem21.match deja initialise */
			elem21.lon = strlen(buffer);

			/* Colles */
			(void) sprintf(buffer, "%s%s",
				mot[idmot], mot[idmot + 1]);
			elem22.conv = convertitmot(buffer, synoff22, &elem22.match);
			strcpy(elem22.buf,buffer);
			elem22.lon = strlen(buffer);

			if (elem21.conv && !elem22.conv) {
				pelem2 = &elem21;
				strcpy(synoff2, synoff21);
			} else if (elem22.conv && !elem21.conv) {
				pelem2 = &elem22;
				strcpy(synoff2, synoff22);
			} else if (elem21.conv && elem22.conv) {
				if (elem21.match.similitude > elem22.match.similitude) {
					pelem2 = &elem21;
					strcpy(synoff2, synoff21);
				} else {
					pelem2 = &elem22;
					strcpy(synoff2, synoff22);
				}
			} else { /* if(!elem21.conv && !elem22.conv) */
				pelem2 = &elem21; /* N'importe */
				strcpy(synoff2, synoff21);
			}

			if (pelem2 != &elem21)
				libereconflits(elem21.match.conflits);
			if (pelem2 != &elem22)
				libereconflits(elem22.match.conflits);
		}

		/* On tente avec les deux suivants */
		elem31.conv = FALSE;
		elem31.match.similitude = 0; /* Evite un avertissement */
		elem31.match.modele = NULL;
		elem31.match.conflits = NULL;
		elem31.lon = 0; /* Evite un avertissement */
		pelem3 = &elem31;

		if (idmot + 2 < nbmots) {

			/* Espaces */
			(void) sprintf(buffer, "%s_%s_%s",
					mot[idmot], mot[idmot + 1],	mot[idmot + 2]);
			elem31.conv = convertitmot(buffer, synoff31, &elem31.match);
			strcpy(elem31.buf,buffer);
			/* elem31.match deja initialise */
			elem31.lon = strlen(buffer);

			/* Colles */
			(void) sprintf(buffer, "%s%s%s",
					mot[idmot], mot[idmot + 1],	mot[idmot + 2]);
			elem32.conv = convertitmot(buffer, synoff32, &elem32.match);
			strcpy(elem32.buf,buffer);
			elem32.lon = strlen(buffer);

			/* Espace + colle */
			(void) sprintf(buffer, "%s_%s%s",
					mot[idmot], mot[idmot + 1],	mot[idmot + 2]);
			elem33.conv = convertitmot(buffer, synoff33, &elem33.match);
			strcpy(elem33.buf,buffer);
			elem33.lon = strlen(buffer);

			/* Colle + Espace */
			(void) sprintf(buffer, "%s%s_%s",
					mot[idmot], mot[idmot + 1],	mot[idmot + 2]);
			elem34.conv = convertitmot(buffer, synoff34, &elem34.match);
			strcpy(elem34.buf,buffer);
			elem34.lon = strlen(buffer);

			/* une valeur de base */
			if (elem31.conv) {
				pelem3 = &elem31;
				strcpy(synoff3, synoff31);
				if (elem32.conv && elem32.match.similitude > pelem3->match.similitude) {
					pelem3 = &elem32;
					strcpy(synoff3, synoff32);
				}
				if (elem33.conv && elem33.match.similitude > pelem3->match.similitude) {
					pelem3 = &elem33;
					strcpy(synoff3, synoff33);
				}
				if (elem34.conv && elem34.match.similitude > pelem3->match.similitude) {
					pelem3 = &elem34;
					strcpy(synoff3, synoff34);
				}
			} else if (elem32.conv) {
				pelem3 = &elem32;
				strcpy(synoff3, synoff32);
				if (elem33.conv && elem33.match.similitude > pelem3->match.similitude) {
					pelem3 = &elem33;
					strcpy(synoff3, synoff33);
				}
				if (elem34.conv && elem34.match.similitude > pelem3->match.similitude) {
					pelem3 = &elem34;
					strcpy(synoff3, synoff34);
				}
			} else if (elem33.conv) {
				pelem3 = &elem33;
				strcpy(synoff3, synoff33);
				if (elem34.conv && elem34.match.similitude 	> pelem3->match.similitude) {
					pelem3 = &elem34;
					strcpy(synoff3, synoff34);
				}
			} else if (elem34.conv) {
				pelem3 = &elem34;
				strcpy(synoff3, synoff34);
			} else {
				pelem3 = &elem31; /* Par desespoir */
				strcpy(synoff3, synoff31);
			}

			if (pelem3 != &elem31)
				libereconflits(elem31.match.conflits);
			if (pelem3 != &elem32)
				libereconflits(elem32.match.conflits);
			if (pelem3 != &elem33)
				libereconflits(elem33.match.conflits);
			if (pelem3 != &elem34)
				libereconflits(elem34.match.conflits);
		}

		/* On tente avec les trois suivants */
		elem41.conv = FALSE;
		elem41.match.similitude = 0; /* Evite un avertissement */
		elem41.match.modele = NULL;
		elem41.match.conflits = NULL;
		elem41.lon = 0; /* Evite un avertissement */
		pelem4 = &elem41;

		if (idmot + 3 < nbmots) {
			(void) sprintf(buffer, "%s_%s_%s_%s",
					mot[idmot], mot[idmot + 1],mot[idmot + 2], mot[idmot + 3]);
			elem41.conv = convertitmot(buffer, synoff4, &elem41.match);
			strcpy(elem41.buf,buffer);
			elem41.lon = strlen(buffer);
		}

		/* On tente avec les quatre suivants */
		elem51.conv = FALSE;
		elem51.match.similitude = 0; /* Evite un avertissement */
		elem51.match.modele = NULL;
		elem51.match.conflits = NULL;
		elem51.lon = 0; /* Evite un avertissement */
		pelem5 = &elem51;

		if (idmot + 4 < nbmots) {
			(void) sprintf(buffer, "%s_%s_%s_%s_%s",
				mot[idmot], mot[idmot + 1], mot[idmot + 2], mot[idmot + 3], mot[idmot + 4]);
			elem51.conv = convertitmot(buffer, synoff5, &elem51.match);
			strcpy(elem51.buf,buffer);
			elem51.lon = strlen(buffer);
		}

		if (pelem1->conv || pelem2->conv || pelem3->conv || pelem4->conv || pelem5->conv) {

			/* Partie critique : que choisir ? C'est shiftreduce() qui decide... */
			sel = shiftreduce(*pelem1, *pelem2, *pelem3, *pelem4, *pelem5);

			switch (sel) {
			case 1:
				sortmot(fd2, synoff1, TRUE, pelem1->match.conflits, &debutligne);
				idmot++;
				break;
			case 2:
				sortmot(fd2, synoff2, TRUE, pelem2->match.conflits, &debutligne);
				idmot += 2;
				break;
			case 3:
				sortmot(fd2, synoff3, TRUE, pelem3->match.conflits, &debutligne);
				idmot += 3;
				break;
			case 4:
				sortmot(fd2, synoff4, TRUE, pelem4->match.conflits, &debutligne);
				idmot += 4;
				break;
			case 5:
				sortmot(fd2, synoff5, TRUE, pelem5->match.conflits, &debutligne);
				idmot += 5;
				break;
			default:
				(void) fprintf(stderr,"Erreur interne : Pb selection impossible");
				exit(-1);
			}

			libereconflits(pelem1->match.conflits);
			libereconflits(pelem2->match.conflits);
			libereconflits(pelem3->match.conflits);
			libereconflits(pelem4->match.conflits);
			libereconflits(pelem5->match.conflits);

			continue;

		}

		/* Bon, de guerre lasse on prend le mot tel quel... */
		sortmot(fd2, mot[idmot], FALSE, NULL, &debutligne);

		idmot++;

	}
}

/* Traduit un fichier en entrée */
static void traduitfichier(const char *nomfic1, const char *nomfic2) {
	BOOL finfichier;
	FILE *fd1, *fd2;

	if ((fd1 = fopen(nomfic1, "rt")) == NULL) {
		(void) fprintf(stderr,"Erreur : Impossible d'ouvrir le fichier en lecture %s\n",nomfic1);
		exit(-1);
	}

	if ((fd2 = fopen(nomfic2, "wt")) == NULL) {
		(void) fprintf(stderr,"Erreur : Impossible d'ouvrir le fichier en ecriture %s\n",
				nomfic2);
		exit(-1);
	}

	for (;;) {

		traduitligne(fd1, fd2, &finfichier);
		if (finfichier)
			break;
		(void) fprintf(fd2, "\n");

	}

	(void) fclose(fd1);
	(void) fclose(fd2);

	return;
}

/* Insère une référence dans le dictionaire */
static void inserereference(const char *ref, const char *synoff) {

	DICO *p;

	for (p = dictionnaire; p; p = p->suiv)
		if (!strcasecmp(p->ref, ref)) {
			(void) fprintf(stderr,"Erreur : lexique : Reference en double %s\n", ref);
			exit(-1);
		}

	p = (DICO *) malloc(sizeof(DICO));

	p->ref = (char *) malloc(strlen(ref) + 1);
	(void) strcpy(p->ref, ref);

	p->synoff = (char *) malloc(strlen(synoff) + 1);
	(void) strcpy(p->synoff, synoff);

	p->lsyn = NULL;

	p->suiv = dictionnaire;
	dictionnaire = p;
}

/* Insère un synonyme d'une référence donnée dans le dictionaire */
static void inseresynonyme(const char *ref, const char *syn) {
	DICO *p;
	LISTESYN *q;

	for (p = dictionnaire; p; p = p->suiv)
		if (!strcasecmp(p->ref, ref))
			break;

	if (p == NULL) {
		(void) fprintf(stderr,"Erreur : filtre : Synonyme de reference absente %s\n", ref);
		exit(-1);
	}

	if (!strcasecmp(p->ref, syn)) {
		(void) fprintf(stderr,"Avertissement : filtre : Synonyme %s en doublon pour reference %s\n",syn, ref);
		return; /* deja sous forme de reference : erreur pas grave*/
	}

	for (q = p->lsyn; q; q = q->suiv)
		if (!strcasecmp(q->val, syn))
			return; /* deja present : erreur pas grave*/

	q = (LISTESYN *) malloc(sizeof(LISTESYN));
	q->val = (char *) malloc(strlen(syn) + 1);

	(void) strcpy(q->val, syn);

	q->suiv = p->lsyn;
	p->lsyn = q;

}

/* Charge le dictionnaire (lexique) à partir d'un fichier */
static void chargelexique(const char *nomfic) {
	FILE *fd;
	char buf1[SIZEMAXLIGNE], ref[SIZEMAXMOT], synoff[SIZEMAXMOT];
	char *p, *q;

	if ((fd = fopen(nomfic, "rt")) == NULL) {
		(void) fprintf(stderr,"Erreur : Impossible d'ouvir le fichier lecture %s\n", nomfic);
		exit(-1);
	}

	for (;;) { /* lignes */

		if (!fgets(buf1, SIZEMAXLIGNE - 1, fd))
			break;

		/* Passe les espaces */
		for (p = buf1; *p && (*p == ' ' || *p == '\t'); p++)
			; /* rien */

		/* 13 pour unix */
		if (*p == ';' || *p == '\n' || *p == 13)
			continue;

		/* Trouve la reference */
		for (q = ref; *p && !(*p == '\n' || *p == 13 || *p == ' ' || *p == '\t'); p++, q++)
			*q = *p;
		*q = EOS;

		/* Passe les espaces */
		for (; *p && (*p == ' ' || *p == '\t'); p++)
			;   /* rien */

		/* Trouve le synonyme officiel */
		for (q = synoff; *p && !(*p == ';' || *p == '\n' || *p == 13 || *p 	== ' ' || *p == '\t'); p++, q++)
			*q = *p;
		*q = EOS;

		inserereference(ref, synoff);

		/* Passe les espaces */
		for (; *p && (*p == ' ' || *p == '\t'); p++)
			;

		if (*p != ';' && *p != '\n' && *p != 13) {
			(void) fprintf(stderr,"Erreur : lexique : elements superflus pour reference %s\n",ref);
			exit(-1);
		}
	}

	(void) fclose(fd);
}

/* Charge le dictionnaire (le filtre)  à partir d'un fichier */
static void chargefiltre(const char *nomfic) {
	FILE *fd;
	char buf1[SIZEMAXLIGNE], ref[SIZEMAXMOT], syn[SIZEMAXMOT];
	char *p, *q;
	int nsyn;

	if ((fd = fopen(nomfic, "rt")) == NULL) {
		(void) fprintf(stderr,"Erreur : Impossible d'ouvrir le fichier en lecture %s\n",nomfic);
		exit(-1);
	}

	for (;;) { /* lignes */

		if (!fgets(buf1, SIZEMAXLIGNE - 1, fd))
			break;

		/* Passe les espaces */
		for (p = buf1; *p && (*p == ' ' || *p == '\t'); p++)
			;	/* rien */

		if (*p == ';' || *p == '\n' || *p == 13)
			continue;

		/* Trouve la reference */
		for (q = ref; *p
				&& !(*p == '\n' || *p == 13 || *p == ' ' || *p == '\t'); p++, q++)
			*q = enleveaccent(*p);
		*q = EOS;

		nsyn = 0;
		for (;;) {

			/* Passe les espaces */
			for (; *p && (*p == ' ' || *p == '\t'); p++)
				;  /* rien */

			if (*p == ';' || *p == '\n' || *p == 13)
				break;

			/* Trouve un synonyme */
			for (q = syn; *p && !(*p == ';' || *p == '\n' || *p == 13 || *p
					== ' ' || *p == '\t'); p++, q++)
				*q = enleveaccent(*p);
			*q = EOS;

			inseresynonyme(ref, syn);

			nsyn++;

		}

		if (nsyn == 0) {
			(void) fprintf(stderr,"Erreur : lexique : Pas de synonyme pour %s\n", ref);
			exit(-1);
		}
	}

	(void) fclose(fd);
}

/* Affiche  le dictionnaire chargé (DEBUG) */
/*
#ifdef DEBUG
static void affdico(void)
{
	DICO *p;
	LISTESYN *q;

	(void) printf("----DICTIONNAIRE---------\n");
	(void) printf("\n");

	for(p = dictionnaire; p; p = p->suiv) {

		(void) printf("%s (%s) : ",p->ref,p->synoff);

		for(q = p->lsyn; q; q = q->suiv)
			(void) printf("%s ",q->val);

		(void) printf("\n");

	}

	(void) printf("-----------------------\n");

	return;
}
#endif
*/

/* Verifie la coherence du dictionnaire avant de continuer */
static void verifiedictionnaire(void) {
	DICO *p, *q;
	LISTESYN *r, *s;
	BOOL erreur;

	erreur = FALSE;
	for (p = dictionnaire; p; p = p->suiv)
		for (q = p->suiv; q; q = q->suiv)
			for (r = p->lsyn; r; r = r->suiv)
				for (s = q->lsyn; s; s = s->suiv)
					if (!strcasecmp(r->val, s->val)) {
						(void) fprintf(stderr,"Erreur : '%s' synonyme à la fois de %s et %s\n",r->val, p->ref, q->ref);
						erreur = TRUE;
					}

	if (erreur) {
		(void) fprintf(stderr, "Erreur: filtre : Revoir le dictionnaire\n");
		exit(-1);
	}

	erreur = FALSE;
	for (p = dictionnaire; p; p = p->suiv)
		if (p->lsyn == NULL) {
			(void) fprintf(stderr, "Erreur : pas de filtre pour '%s'\n", p->ref);
			erreur = TRUE;
		}

	if (erreur) {
		(void) fprintf(stderr, "Erreur : filtre : Revoir le dictionnaire\n");
		exit(-1);
	}

}

#ifdef TESTUNITAIRE
static void deforme(char *mot)
{
	char *p;
	int pos, len;
	char c;

	switch(lrand48() % 5L) {
	case 0 : /* On va supprimer une lettre */
		len = strlen(mot);
		if(len <= 1) /* Refuse si rend chaine vide */
			return;
		pos = lrand48() % len;
		for(p = mot + pos; *p; p++)
			*p = *(p+1);
		break;
	case 1 : /* On va inserer une lettre */
		len = strlen(mot);
		if(len <= 1) /* Refuse si ajoute une lettre a une autre */
			return;
		pos = (lrand48() % len) + 1;
		do
			c = lrand48() % 256;
		while (!isprint(c) || c == ' ');
		for(p = mot + len; p> mot + pos; p--)
			*p = *(p-1);
		mot[len+1] = EOS;
		mot[pos] = c;
		break;
	case 2 : /* On va modifier une lettre */
		len = strlen(mot);
		if(len <= 1) /* Refuse si change une lettre sur un total de une lettre */
			return;
		pos = lrand48() % len;
		do
			c = lrand48() % 256;
		while (!isprint(c) || c == ' ');
		mot[pos] = c;
		break;
	case 3 : /* On va echanger deux lettres */
		len = strlen(mot);
		if(len <= 2) /* Refuse si change deux lettres sur un total de deux lettres */
			return;
		pos = lrand48() % (len-1);
		c = mot[pos];	 /* swap */
		mot[pos] = mot[pos+1];
		mot[pos+1] = c;
		break;
	default :
		/*rien */
		break;
	}
}
#endif

#ifdef TESTUNITAIRE
static void testunitaire(void)
{
	DICO *p;
	LISTESYN *q;
	int n, noref, nbref, nosyn, nbsyn, notest;
	BOOL trouve,different;
	MATCH match;
	char synoff[SIZEMAXMOT];
	char buf[SIZEMAXMOT];
	int nbnontrouves, nbdifferents, nbambiguschanceux, nbambigusmalchanceux, nberreurs;
	LISTECONF *r;

	(void) fprintf(stderr,"Test unitaire :  entree ignoree\n");

	srand48(time(NULL));

	/* Compte les references */
	nbref = 0;
	for(p = dictionnaire; p; p = p->suiv)
		nbref++;

	nbnontrouves = nbdifferents = nbambiguschanceux = nbambigusmalchanceux = nberreurs = 0;

	/* On va faire NBTESTS tests */
	for(notest = 1; notest < NBTESTS; notest++) {

		/* Choix d'une reference au hasard */
		noref = rand() % nbref + 1;
		n = 1;
		for(p = dictionnaire; p; p = p->suiv)
			if(n++ == noref)
				break;

		/* Compte les references */
		nbsyn = 0;
		for(q = p->lsyn; q; q = q->suiv)
			nbsyn++;

		/* Choix d'un synonyme au hasard   */
		nosyn = rand() % nbsyn + 1;
		n = 1;
		for(q = p->lsyn; q; q = q->suiv)
			if(n++ == nosyn)
				break;

		(void) strcpy(buf,q->val);
		deforme(buf);

		/* Test elementaire */
		trouve = convertitmot(buf, synoff, &match);
		different = trouve && strcmp(synoff,p->synoff);

		if(!trouve)
			nbnontrouves++;
		if(different)
			nbdifferents++;
		if(trouve && !different && match.conflits != NULL)
			nbambiguschanceux++;
		if(trouve && different) {
			for(r = match.conflits; r; r = r->suiv)
				if(r->valref == p->synoff) {
					nbambigusmalchanceux++;
					break;
				}
		}

		if(!trouve || different)
			(void) fprintf(stderr,"TEST ref %s (%s) : syn %s : ",p->ref,p->synoff,q->val);
		if(!trouve)
			(void) fprintf(stderr,"deforme en '%s' pas trouve\n",buf);
		if(different) {
			(void) fprintf(stderr,"deforme en '%s' devient %s car ressemble a %s ",buf,synoff,match.modele);
			if(match.conflits) {
				(void) fprintf(stderr,"conflits : ");
				for(r = match.conflits; r; r = r->suiv)
					(void) fprintf(stderr," [?=%s(%s)]",r->valref,r->val);
			} else {
				nberreurs++;
				(void) fprintf(stderr,"GROSSE ERREUR!!! ");
			}
			(void) fprintf(stderr,"\n");
		}

		libereconflits(match.conflits);

	}

	(void) printf("==========================\n");
	(void) printf("RESULTAT : %2.2f %% non trouves, %2.2f %% differents (ambigus : chanceux : %2.2f malchanceux : %2.2f erreurs : %2.2f) donc fiabilite = %2.2f %%\n",
			(((float) nbnontrouves) * 100.0) / ((float) NBTESTS),
			(((float) nbdifferents) * 100.0) / ((float) NBTESTS),
			(((float) nbambiguschanceux) * 100.0) / ((float) NBTESTS),
			(((float) nbambigusmalchanceux) * 100.0) / ((float) NBTESTS),
			(((float) nberreurs) * 100.0) / ((float) NBTESTS),
			((((float) (NBTESTS - (nbnontrouves + nbdifferents))) * 100.0) / ((float) NBTESTS)));
	(void) printf("==========================\n");

}
#endif

int main(int argc, char *argv[])

{
	if (argc != 5) {
		(void) fprintf(stderr,"Arguments %s : <entree> <sortie> <lexique> <filtre>\n",
				argv[0]);
		exit(-1);
	}

	dictionnaire = NULL;

	chargelexique(argv[3]);
	chargefiltre(argv[4]);
	verifiedictionnaire();

#ifdef TESTUNITAIRE
	testunitaire();
#endif

/*
#ifdef DEBUG
	 affdico();
#endif
*/
	traduitfichier(argv[1], argv[2]);

	exit(0);
	return 0; /* evite un avertissement */
}
