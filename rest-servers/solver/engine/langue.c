#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

#define MAXELEM 9

/* Ces variables proviennent de parse.c */
extern int noligne;
extern int lecture;
extern char image[];

char *my_index(char *, char);
char *my_rindex(char *, char);

char *my_index(char *s, char c)
{
	char *p;

	p = NULL;
	for(p = s; *p; p++) {
		if(*p == c)
		return p;
	}
	return NULL;
}

char *my_rindex(char *s, char c)
{
	char *p,*plast;

	plast = NULL;
	for(p = s; *p; p++) {
		if(*p == c)
		plast = p;
	}
	return plast;
}

void addpath(char *s2, const char *s, BOOL carte) {
	char *p;

	if ((p = getenv(nomvarenv)) == NULL) {
		(void) fprintf(
				stderr,
				"Invoke a 'export %s=...' command in order to specify where datafiles are to be found\n",
				nomvarenv);
		exit(-1);
	}

	/* Evite un leger risque si compilateur chatouilleux */
	if (carte) {
		(void) sprintf(s2, "%s/%s/%s", p, NOMFICCARTE, s);
	} else {
		(void) sprintf(s2, "%s/%s", p, s);
	}
}

void cherchechaine(const char *nomfic, const int nomess, char *buf, int n_ptrs,
		...) {
	char *elem[MAXELEM];
	char *pf, *pb, *pe, *pbal;
	int n;
	va_list ap;
	FILE *fd;
	char buflu[TAILLEMESSAGE], nomfic2[TAILLEMESSAGE];
	char *p, *slash;
	char short_messages[TAILLEMOT];
	char messages[TAILLENOMFIC];

	(void) sprintf(short_messages, "DIPLO.%s.TXT", LANGUE);
	addpath(messages, short_messages, FALSE);

	/* On va enlever ce qui precède le dernier slash dans le nom du fichier */
	if ((slash = strrchr(nomfic, '/')) != NULL) {
		slash++;
		(void) strcpy(nomfic2, slash);
	} else
		(void) strcpy(nomfic2, nomfic);

	if ((fd = fopen(messages, "r")) == NULL) {
		(void) fprintf(stderr,
				"Cannot access language dependant datafile %s (%s %d )\n",
				messages, nomfic, nomess);
		exit(-1);
	}

	for (;;) {
		if (fgets(buflu, TAILLEMESSAGE, fd) == NULL) {
			(void) fprintf(
					stderr,
					"Problem reading or locating item (%s %d) in language dependant datafile %s\n",
					nomfic2, nomess, messages);
			exit(-1);
		}
		buflu[strlen(buflu) - 1] = EOS;

		if (strncmp(nomfic2, buflu, strlen(nomfic2)))
			continue;

		if ((p = my_index(buflu, '#')) == NULL) {
			(void) fprintf(
					stderr,
					"Missing separator for item (%s %d) in language dependant datafile %s\n",
					nomfic2, nomess, messages);
			exit(-1);
		}
		p++;

		if (atoi(p) == nomess)
			break;
	}

	(void) fclose(fd);

	if ((p = my_rindex(buflu, '#')) == NULL) {
		(void) fprintf(
				stderr,
				"Missing second separator for item (%s %d) in language dependant datafile %s\n",
				nomfic2, nomess, messages);
		exit(-1);
	}
	p++;

	/* On verifie le nombre d'arguments */
	if (n_ptrs > MAXELEM) {
		(void) fprintf(
				stderr,
				"'%s' : Too many beacons for data of item (%s %d) in language dependant datafile %s\n",
				buflu, nomfic2, nomess, messages);
		exit(-1);
	}

	va_start(ap, n_ptrs);

	/* On recopie les arguments */
	for (n = 0; n < n_ptrs; n++)
		elem[n] = va_arg(ap,char *);

	va_end(ap);

	pf = p;
	pb = buf;

	for (;;) {

		/* Trouve - t - on encore une balise ? */
		if ((pbal = my_index(pf, '%')) == NULL) {

			/* On copie le reste du format */
			for (; *pf;)
				*pb++ = *pf++;
			*pb = EOS;

			break;
		}

		/* On copie jusqu'a la balise */
		for (; pf < pbal;)
			*pb++ = *pf++;
		pbal++;

		/* On recupere le numero de balise */
		n = *pbal - '0' - 1;
		if (n < 0 || n >= n_ptrs) {
			(void) fprintf(
					stderr,
					"'%s' : beacon out of range (%d) for data of item (%s %d) in language dependant datafile %s\n",
					buflu, n + 1, nomfic2, nomess, messages);
			exit(-1);
		}

		/* On copie l'element designe par la balise */
		for (pe = elem[n]; *pe;)
			*pb++ = *pe++;

		/* On se replace juste apres la balise */
		pf = pbal + 1;
	}
}

