#include "includes.h"

#include "define.h"
#include "struct.h"
#include "protos.h"
#include "datas.h"

#define INFINITE 2147483647

typedef enum {
	MOVES, FAILS, MOVE_UNDECIDED
} DECISION_MOVE;
typedef enum {
	GIVEN, CUT, SUPPORT_UNDECIDED
} DECISION_SUPPORT;
typedef enum {
	SUSTAINS, DISLODGED, DISLODGE_UNDECIDED
} DECISION_DISLODGE;
typedef enum {
	PATH, NO_PATH, PATH_UNDECIDED
} DECISION_PATH;
typedef enum {
	FIGHT, NO_FIGHT, FIGHT_UNDECIDED
} DECISION_HEAD_TO_HEAD_BATTLE;
typedef enum {
	CONVOY_PATH, NO_CONVOY_PATH, CONVOY_PATH_UNDECIDED
} DECISION_CONVOY_PATH;
typedef enum {
	PARADOX, NO_PARADOX, PARADOX_UNDECIDED
} DECISION_PARADOX;

typedef struct {
	DECISION_MOVE move;
	DECISION_SUPPORT support;
	DECISION_DISLODGE dislodge;
	int attack_strength_min, attack_strength_max;
	int prevent_strength_min, prevent_strength_max;
	int defend_strength_min, defend_strength_max;
	DECISION_PATH path;
	DECISION_CONVOY_PATH convoy_path;
	DECISION_PARADOX paradox;
	_MOUVEMENT *mouvement;
} _DECISION_UNIT;

typedef struct {
	DECISION_HEAD_TO_HEAD_BATTLE head_to_head_battle;
} _DECISION_TWO_UNIT;

typedef struct {
	int hold_strength_min, hold_strength_max;
	_REGION *region;
} _DECISION_REGION;

typedef/**/LISTE(_UNITE *,NUNITES) _CHAINE;

typedef/**/LISTE(_DECISION_UNIT,NMOUVEMENTS) _DECISION1;
typedef/**/LISTE2(_DECISION_TWO_UNIT,NMOUVEMENTS) _DECISION2;
typedef/**/LISTE(_DECISION_REGION,NREGIONS) _DECISION3;
typedef/**/LISTE(_RETRAITE *,NRETRAITES) _COLLISIONRETRAITE;
typedef/**/LISTE(_REGION *,NREGIONS) _REGIONVIDE;

typedef struct {
	_DECISION1 DECISION1;
	_DECISION2 DECISION2;
	_DECISION3 DECISION3;
} _DECISION;

/* Ces variables proviennent de parse.c */
extern int noligne;

/* Donnees globales */
_DECISION DECISION_OFFICIELLE, CONJONCTURE_DE_TRAVAIL;

static void decritunite(_UNITE *, char *);
static BOOL contextevalidation(_PAYS *pays);
static BOOL mouvementsidentiques(_MOUVEMENT *, _MOUVEMENT *);
static BOOL retraitesidentiques(_RETRAITE *, _RETRAITE *);
static BOOL ajustementsidentiques(_AJUSTEMENT *, _AJUSTEMENT *);
static BOOL retraitepossible(_DELOGEE *);

static BOOL headtohead(_MOUVEMENT *, _MOUVEMENT *);

static _DECISION_UNIT *cherchedecision1(_DECISION *, _MOUVEMENT *);
static _DECISION_TWO_UNIT *cherchedecision2(_DECISION *, _MOUVEMENT *,
		_MOUVEMENT *);
static _DECISION_REGION *cherchedecision3(_DECISION *, _REGION *);
static BOOL valid_convoy(_DECISION *, _ZONE *, _ZONE *, BOOL);
static BOOL move_decision(_DECISION *, _DECISION_UNIT *);
static BOOL support_decision(_DECISION *, _DECISION_UNIT *);
static BOOL dislodge_decision(_DECISION *, _DECISION_UNIT *);
static BOOL attack_strength_decision(_DECISION *, _DECISION_UNIT *);
static BOOL hold_strength_decision(_DECISION *, _DECISION_REGION *);
static BOOL prevent_strength_decision(_DECISION *, _DECISION_UNIT *);
static BOOL defend_strength_decision(_DECISION *, _DECISION_UNIT *);
static BOOL path_decision(_DECISION *, _DECISION_UNIT *);
static BOOL head_to_head_battle_decision(_DECISION *, _DECISION_UNIT *,
		_DECISION_UNIT *);
static BOOL convoy_path_decision(_DECISION *, _DECISION_UNIT *);
static BOOL paradox_decision(_DECISION *, _DECISION_UNIT *);
static BOOL solve_circular(_DECISION *);
static void init_decisions(_DECISION *);
static BOOL all_decisions_made(_DECISION *);
static void assert_decisions_made(_DECISION *);
static void propagation(_DECISION *);
static void resolution_paradoxes1(_DECISION *);
static void resolution_paradoxes2(_DECISION *);
static void creesuppressions(_PAYS *pays, int souhaites);
static void creeconstructions(_PAYS *pays, int souhaites);

static void decision_dump(_DECISION *);

/**************************************************************************
 PHASE AVANT RESOLUTION
 **************************************************************************/

static void decritunite(_UNITE *unite, char *s) {
	(void) sprintf(s, "%s %s%s (%s)", (unite->typeunite == ARMEE ? "A" : "F"),
			unite->zone->region->nom, unite->zone->specificite,
			unite->pays->nom);
}

static BOOL contextevalidation(_PAYS *pays) {
	char *p;

	for (p = OPTIONx; *p; p++)
		if (paysdinitiale(*p) == pays)
			return TRUE;

	return FALSE;
}

static BOOL mouvementsidentiques(_MOUVEMENT *mouv1, _MOUVEMENT*mouv2) {
	if (mouv1->unite != mouv2->unite)
		return FALSE;

	if (mouv1->typemouvement != mouv2->typemouvement)
		return FALSE;

	switch (mouv1->typemouvement) {
	case STAND:
		break;
	case CONVOI:
		if (mouv1->unitepass != mouv2->unitepass)
			return FALSE;
		if (mouv1->zonedest != mouv2->zonedest)
			return FALSE;
		break;
	case SOUTIENOFF:
		if (mouv1->unitepass != mouv2->unitepass)
			return FALSE;
		if (mouv1->zonedest != mouv2->zonedest)
			return FALSE;
		break;
	case ATTAQUE:
		if (mouv1->zonedest != mouv2->zonedest)
			return FALSE;
		break;
	case SOUTIENDEF:
		if (mouv1->unitepass != mouv2->unitepass)
			return FALSE;
		break;
	}

	return TRUE;
}

static BOOL retraitesidentiques(_RETRAITE *ret1, _RETRAITE *ret2) {
	if (ret1->delogee != ret2->delogee)
		return FALSE;

	if (ret1->typeretraite != ret2->typeretraite)
		return FALSE;

	switch (ret1->typeretraite) {
	case SUICIDE:
		break;
	case FUITE:
		if (ret1->zonedest != ret2->zonedest)
			return FALSE;
		break;
	}

	return TRUE;
}

static BOOL ajustementsidentiques(_AJUSTEMENT *ajust1, _AJUSTEMENT *ajust2) {
	if (ajust1->typeajustement != ajust2->typeajustement)
		return FALSE;

	switch (ajust1->typeajustement) {
	case AJOUTE:
		if (ajust1->unite->typeunite != ajust2->unite->typeunite)
			return FALSE;
		if (ajust1->unite->zone != ajust2->unite->zone)
			return FALSE;
		break;
	case SUPPRIME:
		if (ajust1->unite != ajust2->unite)
			return FALSE;
		break;
	}

	return TRUE;
}

static void creesuppressions(_PAYS *pays, int souhaites) {
	int ajustements, el, elrec;
	_UNITE *t, *trec;
	_AJUSTEMENT *u, *v, *w;

	u = AJUSTEMENT.t + AJUSTEMENT.n;
	v = u;

	ajustements = 0;
	while (ajustements < souhaites) {

		trec = NULL;
		for (t = UNITE.t; t < UNITE.t + UNITE.n; t++) {

			/* Pas du pays */
			if (t->pays != pays)
				continue;

			/* Deja supprime */
			for (w = v; w < AJUSTEMENT.t + AJUSTEMENT.n; w++)
				if (w->unite == t)
					break;
			if (w != AJUSTEMENT.t + AJUSTEMENT.n)
				continue;

			/* Par defaut il est pris */
			if (trec == NULL) {
				trec = t;
				continue;
			}

			el = eloignement(t->typeunite, t->zone, pays);
			elrec = eloignement(trec->typeunite, trec->zone, pays);

			/* Si plus loin il passe devant */
			if (el > elrec) {
				trec = t;
				continue;
			}

			if (el == elrec) {

				/* Si c'est une flotte et l'autre une armée il passe devant */
				if (t->typeunite == FLOTTE && trec->typeunite == ARMEE) {
					trec = t;
					continue;
				}

				/* S'il est avant dans l'ordre alphabétique il passe devant */
				if (t->typeunite == trec->typeunite) {
					if (strcmp(t->zone->region->nom, trec->zone->region->nom)
							< 0) {
						trec = t;
						continue;
					}
				}
			}

		} /* for */

		/* On sort de la boucle avec trec = meilleur candidat a la suppression */
		assert(trec != NULL);

		u->typeajustement = SUPPRIME;
		u->unite = trec;

		u->noligne = 0;
		AJUSTEMENT.n++;
		u++;

		ajustements++;

	} /* while */
}

static void creeconstructions(_PAYS *pays, int souhaites) {

	int ajustements;
	TYPEUNITE typeunite;
	TYPEAJUSTEMENT typeajustement;
	_ZONE *zonedest;
	_CENTREDEPART *p, *centredepart;
	_UNITE *q, *unite;

	/* on va se limiter a des armees */
	typeajustement = AJOUTE;
	typeunite = ARMEE;

	ajustements = 0;
	while (ajustements < souhaites) {

		for (zonedest = ZONE.t; zonedest < ZONE.t + ZONE.n; zonedest++) {

			/* la zone doit etre un centre */
			centredepart = NULL;
			for (p = CENTREDEPART.t; p < CENTREDEPART.t + CENTREDEPART.n; p++) {
				if(p->centre->region == zonedest->region) {
					centredepart = p;
					break;
				}
			}
			if(centredepart == NULL) {
				continue;
			}

			/* la zone doit etre un centre du pays */
			if (centredepart->pays != pays) {
				continue;
			}

			/* la zone doit etre possede */
			if (!possede(pays, centredepart->centre)) {
				continue;
			}

			/* la zone doit etre compatible */
			if (!compatibles(typeunite, zonedest)) {
				continue;
			}

			/* la zone doit etre libre */
			if (chercheoccupant(zonedest->region)) {
				continue;
			}

			/* il ne doit pas deja y avoir une construction a cet endroit */
			for (q = UNITEFUTURE.t; q < UNITEFUTURE.t + UNITEFUTURE.n; q++) {
				if(q->zone->region == zonedest->region) {
					break;
				}
			}
			if(q != UNITEFUTURE.t + UNITEFUTURE.n) {
				continue;
			}

			/* unite */
			UNITEFUTURE.t[UNITEFUTURE.n].pays = pays;
			UNITEFUTURE.t[UNITEFUTURE.n].typeunite = typeunite;
			UNITEFUTURE.t[UNITEFUTURE.n].zone = zonedest;
			UNITEFUTURE.t[UNITEFUTURE.n].zonedepart = zonedest;
			unite = UNITEFUTURE.t + UNITEFUTURE.n;
			assert(++UNITEFUTURE.n != NUNITEFUTURES);

			/* construction */
			AJUSTEMENT.t[AJUSTEMENT.n].typeajustement = typeajustement;
			AJUSTEMENT.t[AJUSTEMENT.n].unite = unite;
			AJUSTEMENT.t[AJUSTEMENT.n].noligne = noligne;
			assert(++AJUSTEMENT.n != NAJUSTEMENTS);

			ajustements++;
			break;
		}

	} /* while */

}

void verifmouvements(void) {
	char buf2[TAILLEMOT * 4], buf3[TAILLEMOT * 4];
	_MOUVEMENT *p, *q;
	_UNITE *r, *t;
	_PAYS *s, *pays;
	char buf[TAILLEMESSAGE];
	BOOL doublon;

	pays = NULL; /* Evite un avertissement du compilateur */

	/* Recherche unites sans ordre */
	for (r = UNITE.t; r < UNITE.t + UNITE.n; r++) {
		for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
			if (p->unite == r)
				break;
		if (p == MOUVEMENT.t + MOUVEMENT.n) {
			decritunite(r, buf2);
			cherchechaine(__FILE__, 1, buf, 1, buf2); /*"Manque l'ordre de mouvement de %1"*/
			erreurverif(r->pays, MANQUANT, buf);
		}
	}

	/* Recherche des doublons egaux : on balaie tout */
	doublon = FALSE;
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n - 1; p++)
		for (q = p + 1; q < MOUVEMENT.t + MOUVEMENT.n; q++)
			if (mouvementsidentiques(p, q)) {
				doublon = TRUE;
				pays = p->unite->pays;
				decritunite(q->unite, buf2);
				cherchechaine(__FILE__, 52, buf, 1, buf2); /*" Ordres identiques" */
				avertir(buf);
			}

	if (doublon) {
		cherchechaine(__FILE__, 32, buf, 0); /*"Supprimer le ou les ordre(s) en double" */
		erreurverif(pays, DUPLIQUE, buf);
	}

	/* Recherche des doublons distincts ou égaux : on s'arrete au premier */
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n - 1; p++)
		for (q = p + 1; q < MOUVEMENT.t + MOUVEMENT.n; q++)
			/* Doublon si ordre sur meme unite  */
			if (p->unite == q->unite) {
				noligne = q->noligne;
				decritunite(p->unite, buf2);
				cherchechaine(__FILE__, 2, buf, 1, buf2); /*"Doublon dans les ordres de mouvement sur %1"*/
				erreurverif2(q->unite->pays, DUPLIQUE, buf);
			}

	/* Soutiens ou convois ou attaques non coherents */
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

		switch (p->typemouvement) {

		case SOUTIENOFF:
			for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
				if (q->unite == p->unitepass && !(q->typemouvement == ATTAQUE
						/* Les soutiens n'ont pas besoin de correspondre en cote */
						&& q->zonedest->region == p->zonedest->region)) {
					if (p->unite->pays == p->unitepass->pays) {
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 3, buf, 1, buf2); /*"L'unite %1 soutient offensivement une unite du meme pays qui n'effectue pas le deplacement (=> annule)"*/
						avertir(buf);
					} else if (contextevalidation(p->unitepass->pays)) {
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 46, buf, 1, buf2); /*"L'unite %1 soutient offensivement une unite dont l'ordre est indetermine"*/
						informer(buf);
					}
					break;
				}
			for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
				/* Cerise sur le gateau : on previent qu'incoherence mais ce n'est pas grave ! */
				if (q->unite == p->unitepass && q->typemouvement == ATTAQUE
						&& q->zonedest->region == p->zonedest->region && q->zonedest != p->zonedest) {
					if (p->unite->pays == p->unitepass->pays) {
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 26, buf, 1, buf2); /*"L'unite %1 soutient offensivement une unite du meme pays qui n'effectue pas exactement le deplacement (la cote est differente) (=> accepte)"*/
						avertir(buf);
					}
					break;
				}
			break;

		case CONVOI:
			for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
				if (q->unite == p->unitepass && !(q->typemouvement == ATTAQUE
						&& q->zonedest == p->zonedest)) {
					if (p->unite->pays == p->unitepass->pays) {
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 4, buf, 1, buf2); /*"L'unite %1 convoie une unite du meme pays qui n'effectue pas le convoi (=> annule)"*/
						avertir(buf);
					} else if (contextevalidation(p->unitepass->pays)) {
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 47, buf, 1, buf2); /*"L'unite %1 convoie une unite dont l'ordre est indetermine"*/
						informer(buf);
					}
					break;
				}
			break;

		case SOUTIENDEF:
			for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
				if (q->unite == p->unitepass && q->typemouvement == ATTAQUE) {
					if (p->unite->pays == p->unitepass->pays) {
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 5, buf, 1, buf2); /*"L'unite %1 soutient defensivement une unite du meme pays qui se deplace (=> annule)"*/
						avertir(buf);
					} else if (contextevalidation(p->unitepass->pays)) {
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 48, buf, 1, buf2); /*"L'unite %1 soutient defensivement une unite dont l'ordre est indetermine"*/
						informer(buf);
					}
					break;
				}
			break;

		case ATTAQUE:
			t = chercheoccupant(p->zonedest->region);
			if(t != NULL && t->pays == p->unite->pays) {
				for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++) {
					if (q->unite == t && q->typemouvement != ATTAQUE) {
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 33, buf, 1, buf2); /*"L'unite %1 attaque une unite compatriote qui ne bouge pas "*/
						informer(buf);
					}
				}
			}
			break;

		default:
			continue;

		}
	}

	/* Soutien ou convoi sur convois non obtenu */
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		if (p->valable) {

			switch (p->typemouvement) {

			case SOUTIENOFF:
				if (p->unitepass->typeunite == ARMEE && !armeevoisin(
						p->unitepass->zone, p->zonedest) && !convoiexiste(
						p->unitepass->zone, p->zonedest)) {
					if (empecheconvoi(p->unite, p->unitepass->zone, p->zonedest)) {
						noligne = p->noligne;
						decritunite(p->unite, buf2);
						cherchechaine(__FILE__, 20, buf, 1, buf2); /*"L'unite %1 soutient offensivement une unite qui requiert son propre convoi "*/
						erreurverif2(p->unite->pays, COHERENCE, buf);
					}
					r = unitedupaysempechantconvoi(p->unite->pays,
							p->unitepass->zone, p->zonedest);
					if (r) {
						decritunite(p->unite, buf2);
						decritunite(r, buf3);
						cherchechaine(__FILE__, 6, buf, 2, buf2, buf3); /*"L'unite %1 soutient offensivement une unite qui requiert le convoi de l'unite compatriote  %2 (=> annule)"*/
						avertir(buf);
					}
					for (s = PAYS.t; s < PAYS.t + PAYS.n; s++)
						if (s != p->unite->pays) {
							r = unitedupaysempechantconvoi(s,
									p->unitepass->zone, p->zonedest);
							if (r) {
								if (contextevalidation(s)) {
									decritunite(p->unite, buf2);
									decritunite(r, buf3);
									cherchechaine(__FILE__, 50, buf, 2, buf2,
											buf3); /*"L'unite %1 soutient offensivement une unite qui n'a pas eu le convoi de l'unite %2 d'un autre pays donc dont l'ordre est indetermine"*/
									informer(buf);
								}
							}
						}
					p->valable = FALSE;
				}
				break;

			case CONVOI:
				if (p->unitepass->typeunite == ARMEE && !armeevoisin(
						p->unitepass->zone, p->zonedest) && !convoiexiste(
						p->unitepass->zone, p->zonedest)) {
					r = unitedupaysempechantconvoi(p->unite->pays,
							p->unitepass->zone, p->zonedest);
					if (r) {
						decritunite(p->unite, buf2);
						decritunite(r, buf3);
						cherchechaine(__FILE__, 7, buf, 2, buf2, buf3); /*"L'unite %1 convoie une unite qui requiert le convoi de l'unite compartiote %2 (=> annule)"*/
						avertir(buf);
					}
					for (s = PAYS.t; s < PAYS.t + PAYS.n; s++)
						if (s != p->unite->pays) {
							r = unitedupaysempechantconvoi(s,
									p->unitepass->zone, p->zonedest);
							if (r) {
								if (contextevalidation(s)) {
									decritunite(p->unite, buf2);
									decritunite(r, buf3);
									cherchechaine(__FILE__, 51, buf, 2, buf2,
											buf3); /*"L'unite %1 convoie une unite qui n'a pas eu le convoi de l'unite %2 d'un autre pays donc dont l'ordre est indetermine"*/
									informer(buf);
								}
							}
						}
					p->valable = FALSE;
				}
				break;

			default:
				continue;

			}
		}

	/* Convois non obtenu */
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		if (p->valable) {

			switch (p->typemouvement) {

			case ATTAQUE:
				if (p->unite->typeunite == ARMEE && !armeevoisin(
						p->unite->zone, p->zonedest) && !convoiexiste(
						p->unite->zone, p->zonedest)) {
					r = unitedupaysempechantconvoi(p->unite->pays,
							p->unite->zone, p->zonedest);
					if (r) {
						decritunite(p->unite, buf2);
						decritunite(r, buf3);
						cherchechaine(__FILE__, 8, buf, 2, buf2, buf3); /*"L'unite %1 requiert pour son déplacement le convoi de l'unite compatriote %2 (=> annule)"*/
						avertir(buf);
					}
					for (s = PAYS.t; s < PAYS.t + PAYS.n; s++)
						if (s != p->unite->pays) {
							r = unitedupaysempechantconvoi(s, p->unite->zone,
									p->zonedest);
							if (r) {
								if (contextevalidation(s)) {
									decritunite(p->unite, buf2);
									decritunite(r, buf3);
									cherchechaine(__FILE__, 49, buf, 2, buf2,
											buf3); /*"L'unite %1 a besoin du convoi de l'unite %2 dont l'ordre est indetermine"*/
									informer(buf);
								}
							}
						}
					p->valable = FALSE;
				}
				break;

			default:
				continue;

			}
		}
}

void verifretraites(void) {
	char buf[TAILLEMESSAGE];
	char buf2[TAILLEMOT * 4];
	_RETRAITE *p, *q, **s;
	_DELOGEE *r;
	_PAYS *pays;
	_COLLISIONRETRAITE COLLISIONRETRAITE;
	BOOL doublon;

	pays = NULL; /* Evite un avertissement du compilateur */

	/* Recherche des unites sans ordre */
	for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++) {
		for (p = RETRAITE.t; p < RETRAITE.t + RETRAITE.n; p++)
			if (p->delogee == r)
				break;
		if (p == RETRAITE.t + RETRAITE.n) {
			decritunite(r->unite, buf2);
			cherchechaine(__FILE__, 9, buf, 1, buf2); /*"Manque la retraite de %1"*/
			erreurverif(r->unite->pays, MANQUANT, buf);
		}
	}

	/* Recherche des doublons egaux : on balaie tout */
	doublon = FALSE;
	for (p = RETRAITE.t; p < RETRAITE.t + RETRAITE.n - 1; p++)
		for (q = p + 1; q < RETRAITE.t + RETRAITE.n; q++)
			if (retraitesidentiques(p, q)) {
				doublon = TRUE;
				pays = p->delogee->unite->pays;
				decritunite(q->delogee->unite, buf2);
				cherchechaine(__FILE__, 53, buf, 1, buf2); /*" Ordres identiques" */
				avertir(buf);
			}

	if (doublon) {
		cherchechaine(__FILE__, 32, buf, 0); /*"Supprimer le ou les ordre(s) en double" */
		erreurverif(pays, DUPLIQUE, buf);
	}

	/* Recherche des doublons distincts ou égaux : on s'arrete au premier */
	for (p = RETRAITE.t; p < RETRAITE.t + RETRAITE.n - 1; p++)
		for (q = p + 1; q < RETRAITE.t + RETRAITE.n; q++)
			/* Doublon si ordre sur meme unite delogee */
			if (p->delogee == q->delogee) {
				noligne = q->noligne;
				decritunite(p->delogee->unite, buf2);
				cherchechaine(__FILE__, 10, buf, 1, buf2); /*"Doublon dans les retraites sur %1"*/
				erreurverif2(q->delogee->unite->pays, DUPLIQUE, buf);
			}

	/* Recherche des collisions */
	COLLISIONRETRAITE.n = 0;
	for (p = RETRAITE.t; p < RETRAITE.t + RETRAITE.n; p++)
		for (q = RETRAITE.t; q < RETRAITE.t + RETRAITE.n; q++) {
			if (p != q && p->typeretraite == FUITE && q->typeretraite == FUITE
					&& p->zonedest->region == q->zonedest->region) {
				for (s = COLLISIONRETRAITE.t; s < COLLISIONRETRAITE.t
						+ COLLISIONRETRAITE.n; s++)
					if (*s == p)
						break;
				if (s == COLLISIONRETRAITE.t + COLLISIONRETRAITE.n)
					COLLISIONRETRAITE.t[COLLISIONRETRAITE.n++] = p;
				q = RETRAITE.t + RETRAITE.n;
				continue;
			}
		}

	if (strcmp(NOMPROGRAMME, "JOUEUR")) { /* ne pas afficher si appel du joueur */
		for (s = COLLISIONRETRAITE.t; s < COLLISIONRETRAITE.t
				+ COLLISIONRETRAITE.n; s++) {
			decritunite((*s)->delogee->unite, buf2);
			cherchechaine(__FILE__, 11, buf, 1, buf2); /*"Retraite de %1 en collision (=> annule)"*/
			informer(buf);
			(*s)->valable = FALSE;
		}
	}
}

void verifajustements(void) {
	char *p;
	char buf2[TAILLEMOT * 4], buf3[TAILLEMOT * 4];
	_PAYS *r, *pays;
	_AJUSTEMENT *u, *v;
	int possessions, unites, ajustements, possibles, souhaites;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER], bufn2[TAILLEENTIER], bufn3[TAILLEENTIER],
			bufn4[TAILLEENTIER], bufn5[TAILLEENTIER];
	BOOL doublon;

	pays = NULL; /* Evite un avertissement du compilateur */

	/* Recherche des doublons egaux : on balaie tout */
	doublon = FALSE;
	for (u = AJUSTEMENT.t; u < AJUSTEMENT.t + AJUSTEMENT.n - 1; u++)
		for (v = u + 1; v < AJUSTEMENT.t + AJUSTEMENT.n; v++)
			/* Doublon construction ou suppression sur meme region */
			if (ajustementsidentiques(u, v)) {
				doublon = TRUE;
				pays = u->unite->pays;
				decritunite(v->unite, buf2);
				switch (u->typeajustement) {
				case AJOUTE:
					cherchechaine(__FILE__, 54, buf, 1, buf2); /*" Ordres identiques" */
					avertir(buf);
					break;
				case SUPPRIME:
					cherchechaine(__FILE__, 55, buf, 1, buf2); /*" Ordres identiques" */
					avertir(buf);
					break;
				}
			}

	if (doublon) {
		cherchechaine(__FILE__, 32, buf, 0); /*"Supprimer le ou les ordre(s) en double" */
		erreurverif(pays, DUPLIQUE, buf);
	}

	/* Recherche des doublons distincts ou égaux construction : on s'arrete au premier */
	for (u = AJUSTEMENT.t; u < AJUSTEMENT.t + AJUSTEMENT.n - 1; u++)
		for (v = u + 1; v < AJUSTEMENT.t + AJUSTEMENT.n; v++)
			/* Doublon construction  sur meme region */
			if (u->typeajustement == AJOUTE && v->typeajustement == AJOUTE
					&& u->unite->zone->region == v->unite->zone->region) {
				noligne = v->noligne;
				decritunite(u->unite, buf2);
				decritunite(v->unite, buf3);
				cherchechaine(__FILE__, 12, buf, 2, buf2, buf3); /*"Doublon dans les ajustements pour %1 et %2"*/
				erreurverif2(v->unite->pays, DUPLIQUE, buf);
			}

	/* Recherche des doublons distincts ou égaux suppression : on s'arrete au premier */
	for (u = AJUSTEMENT.t; u < AJUSTEMENT.t + AJUSTEMENT.n - 1; u++)
		for (v = u + 1; v < AJUSTEMENT.t + AJUSTEMENT.n; v++)
			/* Doublon suppression d'une meme unite */
			if (u->typeajustement == SUPPRIME && v->typeajustement == SUPPRIME
					&& u->unite == v->unite) {
				noligne = v->noligne;
				decritunite(u->unite, buf2);
				cherchechaine(__FILE__, 31, buf, 1, buf2); /*"Doublon dans les ajustements pour %1 */
				erreurverif2(v->unite->pays, DUPLIQUE, buf);
			}

	for (r = PAYS.t; r < PAYS.t + PAYS.n; r++) {

		lesajustements(r, &possessions, &unites, &possibles);
		souhaites = INF(possessions - unites, possibles);

		ajustements = 0;
		noligne = 0;
		for (u = AJUSTEMENT.t; u < AJUSTEMENT.t + AJUSTEMENT.n; u++)
			if (u->unite->pays == r) {
				assert(u->typeajustement == AJOUTE || u->typeajustement == SUPPRIME);
				switch (u->typeajustement) {
				case AJOUTE:
					if (souhaites == 0) {
						noligne = u->noligne;
						cherchechaine(__FILE__, 15, buf, 0); /*"Construction  alors que rien n'est attendu"*/
						erreurverif2(r, COHERENCE, buf);
					}
					if (souhaites < 0) {
						noligne = u->noligne;
						cherchechaine(__FILE__, 13, buf, 0); /*"Construction alors qu'une ou des suppressions sont attendues"*/
						erreurverif2(r, COHERENCE, buf);
					}
					ajustements++;
					break;
				case SUPPRIME:
					if (souhaites == 0) {
						noligne = u->noligne;
						cherchechaine(__FILE__, 16, buf, 0); /*"Suppression alors que rien n'est attendu"*/
						erreurverif2(r, COHERENCE, buf);
					}
					if (souhaites > 0) {
						noligne = u->noligne;
						cherchechaine(__FILE__, 14, buf, 0); /*"Suppression alors qu'une ou des constructions sont attendues"*/
						erreurverif2(r, COHERENCE, buf);
					}
					ajustements--;
					break;
				}
			}

		/* Maintenant on est forcement dans le cas ou les ajustements sont tous dans le bon sens */

		/* On affiche un résumé complet de la situation */
		if (ajustements != souhaites) {
			for (p = OPTIONx; *p; p++)
				if (paysdinitiale(*p) == r)
					break;
			if (*p == EOS) { /* Pas parmi les exclus */
				(void) sprintf(bufn1, "%d", ajustements);
				(void) sprintf(bufn2, "%d", unites);
				(void) sprintf(bufn3, "%d", possessions);
				(void) sprintf(bufn4, "%d", possibles);
				(void) sprintf(bufn5, "%d", souhaites);
				if (souhaites > 0) {
					cherchechaine(__FILE__, 18, buf, 5, bufn1, bufn2, bufn3,
							bufn4, bufn5); /*"Ajustements : %1 mauvais chiffre : (%2 unite(s), %3 centre(s), %4 centre(s) libre(s) => %5 ajustement(s))"*/
					informer(buf);
				}
				if (souhaites < 0) {
					cherchechaine(__FILE__, 19, buf, 4, bufn1, bufn2, bufn3,
							bufn5); /*"Ajustements : %1 mauvais chiffre : (%2 unite(s), %3 centre(s), => %4 ajustement(s))"*/
					informer(buf);
				}
			}
		}

		/* 3 cas clairs d'erreur */
		if (souhaites < 0 && abs(ajustements) < abs(souhaites)) {
			(void) sprintf(bufn1, "%d", abs(souhaites));
			cherchechaine(__FILE__, 27, buf, 1, bufn1); /*"Suppression de %1 unité(s) attendue, moins de suppressions qu'attendu"*/
			erreurverif(r, COHERENCE, buf);
		}
		if (souhaites < 0 && abs(ajustements) > abs(souhaites)) {
			(void) sprintf(bufn1, "%d", abs(souhaites));
			cherchechaine(__FILE__, 28, buf, 1, bufn1); /*"Suppression de %1 unité(s) attendue, plus de suppressions qu'attendu"*/
			erreurverif(r, COHERENCE, buf);
		}
		if (souhaites > 0 && ajustements > souhaites) {
			(void) sprintf(bufn1, "%d", souhaites);
			cherchechaine(__FILE__, 29, buf, 1, bufn1); /*"Construction de %1 unité(s) attendue, plus de constructions qu'attendu"*/
			erreurverif(r, COHERENCE, buf);
		}

		/* Un cas d'erreur ou pas */
		if (souhaites > 0 && ajustements < souhaites) {
			for (p = OPTIONx; *p; p++)
				if (paysdinitiale(*p) == r)
					break;
			if (*p == EOS) { /* Pas parmi les exclus */
				(void) sprintf(bufn1, "%d", souhaites - ajustements);
				cherchechaine(__FILE__, 17, buf, 2, r->nom, bufn1); /*"Ajustements %1 : encore %2 construction(s) autorisee(s)"*/
				informer(buf);
				(void) sprintf(bufn1, "%d", souhaites);
				cherchechaine(__FILE__, 30, buf, 1, bufn1); /*"Construction de %1 unité(s) attendue, moins de constructions qu'attendu"*/
				avertir(buf);
			}
		}
	}
}


void creemouvements(_PAYS *pays) {
	_UNITE *p;
	_MOUVEMENT *q;

	q = MOUVEMENT.t + MOUVEMENT.n;
	for (p = UNITE.t; p < UNITE.t + UNITE.n; p++)
		if (p->pays == pays) {
			q->unite = p;
			q->typemouvement = STAND;
			q->zonedest = p->zone;
			q->valable = TRUE;
			q->coupe = FALSE;
			q->dedaigne = FALSE;
			q->paradoxe = FALSE;
			q->noligne = 0;
			MOUVEMENT.n++;
			q++;
		}
}

void creeretraites(_PAYS *pays) {
	_DELOGEE *p;
	_RETRAITE *q;
	_ZONE *r, *rrec;
	int el, elrec;

	q = RETRAITE.t + RETRAITE.n;
	for (p = DELOGEE.t; p < DELOGEE.t + DELOGEE.n; p++)
		if (p->unite->pays == pays) {
			rrec = NULL;
			if (OPTIONR) {

				for (r = ZONE.t; r < ZONE.t + ZONE.n; r++)
					if (compatibles(p->unite->typeunite, r)
							&& ((p->unite->typeunite == FLOTTE && flottevoisin(
									p->unite->zone, r)) || (p->unite->typeunite
									== ARMEE && armeevoisin(p->unite->zone, r)))
							&& chercheoccupant(r->region) == NULL
							&& !interditretraite(r->region) && r->region
							!= p->zoneorig->region) {

						if (rrec == NULL)
							rrec = r;
						else {
							el = eloignement(p->unite->typeunite, r, pays);
							elrec
									= eloignement(p->unite->typeunite, rrec,
											pays);
							if (el < elrec)
								rrec = r;
							else if (el == elrec) {
								if (strcmp(r->region->nom, rrec->region->nom)
										> 0 || (strcmp(r->region->nom,
										rrec->region->nom) == 0 && strcmp(
										r->specificite, rrec->specificite) > 0))
									rrec = r;
							}
						}
					}
			}
			q->delogee = p;
			q->valable = TRUE;
			q->noligne = 0;
			if (rrec == NULL)
				q->typeretraite = SUICIDE;
			else {
				q->typeretraite = FUITE;
				q->zonedest = rrec;
			}
			RETRAITE.n++;
			q++;

		}
}

void creeajustements(_PAYS *pays) {
	int possessions, unites, possibles, souhaites;

	lesajustements(pays, &possessions, &unites, &possibles);

	/* cas ou on supprime */
	if(possessions < unites) {
		souhaites = unites - possessions;
		creesuppressions(pays, souhaites); 
	}

	/* cas ou on construit */
	if(possessions > unites) {
		souhaites = INF(possessions - unites, possibles);
		creeconstructions(pays, souhaites); 
	}
}


/**************************************************************************
 PHASE APRES RESOLUTION
 **************************************************************************/

void modifmouvements(void) {
	_MOUVEMENT *p;

	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		if (p->typemouvement == ATTAQUE && p->valable)
			p->unite->zone = p->zonedest;
}

void modifretraites(void) {
	_RETRAITE *p;
	_UNITE *q,*s;
	_DELOGEE *r;
	
	UNITEFUTURE.n = 0;
	for (p = RETRAITE.t; p < RETRAITE.t + RETRAITE.n; p++)
		if (p->typeretraite == FUITE && p->valable)

			p->delogee->unite->zone = p->zonedest;

		else {
		
			/* Soit elle s'est dispersee, soit elle a manque sa retraite */

			/* -> on va deplacer l'unite a la fin pour faire office de suppression */

			/* repere position unite qui va s'evaporer */
			s = p->delogee->unite;
			
			/* recopie de l'unite a supprimer vers les "fantomes" */
			UNITEFUTURE.t[UNITEFUTURE.n].typeunite = s->typeunite;
			UNITEFUTURE.t[UNITEFUTURE.n].zone = s->zone;
			UNITEFUTURE.t[UNITEFUTURE.n].zonedepart	= s->zonedepart;
			UNITEFUTURE.t[UNITEFUTURE.n].pays = s->pays;
			UNITEFUTURE.n++;
			assert(UNITEFUTURE.n != NUNITEFUTURES);
			
			/* repere position unite destination */
			q = UNITEFUTURE.t + UNITEFUTURE.n - 1;

			/* -> modifie le pointeur de la delogee (victime) */
			for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
				if (r->unite == s)
					break;
			if (r != DELOGEE.t + DELOGEE.n)
				r->unite = q;

			/* -> modifie le pointeur de la delogee (bourreau) */
			for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
				if (r->uniteorig == s)
					break;
			if (r != DELOGEE.t + DELOGEE.n)
				r->uniteorig = q;

			/* On va mettre la derniere a sa place qui s'est liberee */

			/* repere position unite a deplacer */
			q = UNITE.t + UNITE.n - 1;

			/* recopie  */
			s->typeunite = q->typeunite;
			s->zone = q->zone;
			s->zonedepart = q->zonedepart;
			s->pays = q->pays;
			UNITE.n--;

			/* -> modifie le pointeur de la delogee (victime) aussi pour l'autre unite deplacee */
			for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
				if (r->unite == q)
					break;
			if (r != DELOGEE.t + DELOGEE.n)
				r->unite = s;

			/* -> modifie le pointeur de la delogee (bourreau) aussi pour l'autre unite deplacee */
			for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
				if (r->uniteorig == q)
					break;
			if (r != DELOGEE.t + DELOGEE.n)
				r->uniteorig = s;
				
		}

	INTERDIT.n = 0;
}

void modifajustements(void) {
	_AJUSTEMENT *p, *r;
	_UNITE *q;

	for (p = AJUSTEMENT.t; p < AJUSTEMENT.t + AJUSTEMENT.n; p++)
		switch (p->typeajustement) {

		case AJOUTE:

			UNITE.t[UNITE.n].typeunite = p->unite->typeunite;
			UNITE.t[UNITE.n].zone = p->unite->zone;
			UNITE.t[UNITE.n].zonedepart = p->unite->zone;
			UNITE.t[UNITE.n].pays = p->unite->pays;
			UNITE.n++;
			assert(UNITE.n != NUNITES);
			break;

		case SUPPRIME:
			assert(UNITE.n != 0);

			/* -> sauvegarde unite a supprimer */
			UNITEFUTURE.t[UNITEFUTURE.n].typeunite = p->unite->typeunite;
			UNITEFUTURE.t[UNITEFUTURE.n].zone = p->unite->zone;
			UNITEFUTURE.t[UNITEFUTURE.n].zonedepart = p->unite->zonedepart;
			UNITEFUTURE.t[UNITEFUTURE.n].pays = p->unite->pays;
			UNITEFUTURE.n++;
			assert(UNITEFUTURE.n != NUNITEFUTURES);

			/* -> va deplacer l'unite a la fin pour faire office de suppression */
			q = UNITE.t + UNITE.n - 1;

			/* -> modifie le pointeur de l'ordre aussi pour l'unite deplacee */
			for (r = AJUSTEMENT.t; r < AJUSTEMENT.t + AJUSTEMENT.n; r++)
				if (r->unite == q)
					break;
			if (r != AJUSTEMENT.t + AJUSTEMENT.n)
				r->unite = p->unite;

			/* -> deplace l'unite */
			p->unite->typeunite = q->typeunite;
			p->unite->zone = q->zone;
			p->unite->zonedepart = q->zonedepart;
			p->unite->pays = q->pays;
			UNITE.n--;

			/* modif pointeur delogee */
			p->unite = UNITEFUTURE.t + UNITEFUTURE.n - 1;

			break;
		}
}

void dupliquepossessions(void) {
	_POSSESSION *p;

	for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++) {
		POSSESSIONAVANT.t[POSSESSIONAVANT.n].pays = p->pays;
		POSSESSIONAVANT.t[POSSESSIONAVANT.n].centre = p->centre;
		POSSESSIONAVANT.n++;
	}
}

void modifpossessions(void) {
	char buf[TAILLEMESSAGE];
	_POSSESSION *p;
	_UNITE *q;
	_CENTRE *r;
	_PAYS *s;
	BOOL changement;
	int ncentres;

	changement = FALSE;
	for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++)
		if ((q = chercheoccupant(p->centre->region)) != NULL)
			if (q->pays != p->pays) {
				changement = TRUE;
				if (OPTIONw) {
					cherchechaine(__FILE__, 21, buf, 3, p->centre->region->nom,
							p->pays->nom, q->pays->nom); /*"Le centre %1 change de proprietaire : %2 -> %3"*/
					informer(buf);
				}
				p->pays = q->pays;
				continue;
			}

	for (q = UNITE.t; q < UNITE.t + UNITE.n; q++)
		for (r = CENTRE.t; r < CENTRE.t + CENTRE.n; r++)
			if (r->region == q->zone->region) {
				for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++)
					if (p->centre->region == q->zone->region)
						break;

				if (p == POSSESSION.t + POSSESSION.n) {
					changement = TRUE;
					if (OPTIONw) {
						cherchechaine(__FILE__, 22, buf, 2, r->region->nom,
								q->pays->nom); /*"Le centre %1 a maintenant un proprietaire : %2"*/
						informer(buf);
					}
					POSSESSION.t[POSSESSION.n].pays = q->pays;
					POSSESSION.t[POSSESSION.n++].centre = r;
				}
			}

	if (changement) {
		SAISONMODIF = SAISON;
		for (s = PAYS.t; s < PAYS.t + PAYS.n; s++) {
			ncentres = 0;
			for (p = POSSESSION.t; p < POSSESSION.t + POSSESSION.n; p++)
				if (p->pays == s)
					ncentres++;
			if (ncentres > (CENTRE.n / 2)) {
				cherchechaine(__FILE__, 23, buf, 1, s->nom); /*"La partie est finie, le joueur %1 est declare vainqueur"*/
				avertir(buf);
			}
		}

	} else if (OPTIONS) {
		if (SAISON >= SAISONMODIF + BLOCAGE * 5) {
			cherchechaine(__FILE__, 24, buf, 0); /*"La partie est bloquee, tous les joueurs survivants sont declares vainqueurs"*/
			avertir(buf);
		}
	}

	assert(SAISONMODIF <= SAISON);
}

void calculedisparitions(void) {
	char buf[TAILLEMESSAGE];
	_PAYS *p;
	_POSSESSION *q;
	int ncentres, ncentresavant;

	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++) {

		ncentresavant = 0;
		for (q = POSSESSIONAVANT.t; q < POSSESSIONAVANT.t + POSSESSIONAVANT.n; q++) {
			if(q->pays != p)
				continue;
			ncentresavant++;
		}

		ncentres = 0;
		for (q = POSSESSION.t; q < POSSESSION.t + POSSESSION.n; q++) {
			if(q->pays != p)
				continue;
			ncentres++;
		}

		if(ncentres == 0 && ncentresavant > 0) {

			if (OPTIONw) {
				cherchechaine(__FILE__, 25, buf, 1, p->nom); /*"Le pays %1 vient de disparaitre de la partie"*/
				avertir(buf);
			}

			DISPARITION.t[DISPARITION.n].pays = p;
			DISPARITION.t[DISPARITION.n].annee = ANNEEZERO + (SAISON / NSAISONS);
			DISPARITION.n++;
		}

	}

	assert(DISPARITION.n != NDISPARITIONS);
}

void suppressionelimines(void) {
	char buf[TAILLEMESSAGE];
	_PAYS *p;
	_UNITE *q, *s;
	_DELOGEE *r;
	int ncent, nunit, najustementsposs;

	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++) {

		calculajustements(p, &ncent, &nunit, &najustementsposs);

		if (nunit > 0 && ncent == 0) {

			if (strcmp(NOMPROGRAMME, "JOUEUR")) { /* ne pas afficher si appel du joueur */
				if (OPTIONw) {
					cherchechaine(__FILE__, 45, buf, 1, p->nom); /*"Suppression des unites du pays %1"*/
					informer(buf);
				}
			}
			for (q = UNITE.t; q < UNITE.t + UNITE.n; q++)
				if (q->pays == p) {

					for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
						if (r->unite == q)
							break;

					/* LA DELOGEE (SI DELOGEE IL Y A) POINTE TJR SUR UNE UNITE */
					if (r < DELOGEE.t + DELOGEE.n) {
						/* SAUVEGARDE UNITE A SUPPRIMER */
						UNITEFUTURE.t[UNITEFUTURE.n].typeunite = q->typeunite;
						UNITEFUTURE.t[UNITEFUTURE.n].zone = q->zone;
						UNITEFUTURE.t[UNITEFUTURE.n].zonedepart = q->zonedepart;
						UNITEFUTURE.t[UNITEFUTURE.n].pays = q->pays;
						UNITEFUTURE.n++;
						assert(UNITEFUTURE.n != NUNITEFUTURES);
						r->unite = UNITEFUTURE.t + UNITEFUTURE.n - 1;
					}

					/* SUPPRESSION UNITE */
					assert(UNITE.n != 0);
					/* reperage unite la plus haute */
					s = UNITE.t + UNITE.n - 1;
					/* decalage d'une retraite eventuelle vers l'unite la plus haute */
					for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
						if (r->unite == s)
							break;
					if (r < DELOGEE.t + DELOGEE.n)
						r->unite = q;
					/* suppression */
					q->typeunite = s->typeunite;
					q->zone = s->zone;
					q->zonedepart = s->zonedepart;
					q->pays = s->pays;
					UNITE.n--;
				}
		}
	}
}

void finretraites(void) {
	DELOGEE.n = 0;
}

/**************************************************************************
 RESOLUTION  (MOUVEMENTS SEULEMENT)
 **************************************************************************/

static BOOL retraitepossible(_DELOGEE *delogee)
/* Vrai si l'unite peut faire retraite quelque part */
{
	_ARMEEVOISIN *p;
	_FLOTTEVOISIN *q;

	switch (delogee->unite->typeunite) {
	case ARMEE:
		for (p = ARMEEVOISIN.t; p < ARMEEVOISIN.t + ARMEEVOISIN.n; p++)
				/* marche aussi avec le fonction chercheoccupant() */
			if (p->zone1 == delogee->unite->zone && chercheoccupantnondeloge(
					p->zone2->region) == NULL && p->zone2->region
					!= delogee->zoneorig->region && !interditretraite(
					p->zone2->region))
				return TRUE;
		break;

	case FLOTTE:
		for (q = FLOTTEVOISIN.t; q < FLOTTEVOISIN.t + FLOTTEVOISIN.n; q++)
			/* marche aussi avec le fonction chercheoccupant() */
			if (q->zone1 == delogee->unite->zone && chercheoccupantnondeloge(
					q->zone2->region) == NULL && q->zone2->region
					!= delogee->zoneorig->region && !interditretraite(
					q->zone2->region))
				return TRUE;
		break;
	}

	return FALSE;
}

void calculinterdites(void)
/* Detecte les regions interdites en retraite */
{
	_MOUVEMENT *p, *q;
	_UNITE *r;
	_REGION *s, **t;
	_REGIONVIDE REGIONVIDE;

	REGIONVIDE.n = 0;
	/* Trouve les regions vides */
	for (s = REGION.t; s < REGION.t + REGION.n; s++) {

		/* Doit etre vacante */
		for (r = UNITE.t; r < UNITE.t + UNITE.n; r++)
			if (r->zone->region == s)
				break;
		if (r < UNITE.t + UNITE.n)
			continue;

		REGIONVIDE.t[REGIONVIDE.n] = s;
		REGIONVIDE.n++;
	}

	INTERDIT.n = 0;
	for (t = REGIONVIDE.t; t < REGIONVIDE.t + REGIONVIDE.n; t++) {

		/* Blocage reel : au moins deux unites vont s'y heurter */
		for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n - 1; p++) {

			/* Une premiere unite doit s'y casser les dents et pas a cause de convoi */
			if (p->typemouvement != ATTAQUE)
				continue;

			if (p->zonedest->region != *t)
				continue;

			if (p->valable)
				continue;

			if (convoinecessaire(p) && !convoivalide(p->unite->zone,
					p->zonedest))
				continue;

			for (q = p + 1; q < MOUVEMENT.t + MOUVEMENT.n; q++) {

				/* Une deuxieme unite doit s'y casser les dents et pas a cause de convoi */
				if (q->typemouvement != ATTAQUE)
					continue;

				if (q->zonedest->region != *t)
					continue;

				if (q->valable)
					continue;

				if (!(convoinecessaire(q) && !convoivalide(q->unite->zone,
						q->zonedest))) {

					INTERDIT.t[INTERDIT.n].region = *t;
					INTERDIT.n++;
					assert(INTERDIT.n <= NINTERDITS);

					p = MOUVEMENT.t + MOUVEMENT.n - 1;
					break;
				}
			}
		}
	}
}

void calculaneanties(void)
/* Detecte les unites aneanties (sans retraite possible) */
{
	_DELOGEE *p;

	ANEANTIE.n = 0;
	for (p = DELOGEE.t; p < DELOGEE.t + DELOGEE.n; p++)
		if (!retraitepossible(p)) {
			ANEANTIE.t[ANEANTIE.n].delogee = p;
			ANEANTIE.n++;
			assert(ANEANTIE.n <= NANEANTIES);
		}
}

void suppressionelimines2(void) {
	char buf[TAILLEMESSAGE];
	_PAYS *p;
	_UNITE *q;
	_CENTRE *t;
	_POSSESSION *u;
	_DELOGEE *r, *x;
	_ARMEEVOISIN *v, *vv;
	_FLOTTEVOISIN *w, *ww;
	BOOL retraitecentrepossible, collisionpossible;

	for (p = PAYS.t; p < PAYS.t + PAYS.n; p++) {
		
		for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
			if (r->unite->pays == p)
				break;
		if (r == DELOGEE.t + DELOGEE.n)
			continue; /* le pays n'a pas d'unite delogee */

		for (t = CENTRE.t; t < CENTRE.t + CENTRE.n; t++) {

			for (u = POSSESSION.t; u < POSSESSION.t + POSSESSION.n; u++) {
				if (u->centre != t)
					continue;
				if (u->pays != p)
					continue;
				q = chercheoccupantnondeloge(t->region);
				/* ce centre du pays n'est pas occupe par une unite d'un autre pays */
				if (q == NULL || q->pays == p)
					break;
			}

			if(u < POSSESSION.t + POSSESSION.n)
				break;
		}

		if (t < CENTRE.t + CENTRE.n)
			continue; /* un centre du pays n'est pas occupe par une unite d'un autre pays */

		for (q = UNITE.t; q < UNITE.t + UNITE.n; q++) {
			if (q->pays != p)
				continue;
			/* Pas delogee */
			for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++)
				if (r->unite == q)
					break;
			if(r < DELOGEE.t + DELOGEE.n)
				continue;
			for (t = CENTRE.t; t < CENTRE.t + CENTRE.n; t++)
				if (t->region == q->zone->region)
					break;
			/* cette unite du pays occupe un centre */
			if (t < CENTRE.t + CENTRE.n)
				break;
		}

		if (q < UNITE.t + UNITE.n)
			continue; /* une unite du pays occupe un centre */

		retraitecentrepossible = collisionpossible = FALSE;
		for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++) {

			if (r->unite->pays != p)
				continue;

			switch (r->unite->typeunite) {
			case ARMEE:

				for (v = ARMEEVOISIN.t; v < ARMEEVOISIN.t + ARMEEVOISIN.n; v++)
					if (v->zone1 == r->unite->zone &&
							/* marche aussi avec le fonction chercheoccupant() */
							chercheoccupantnondeloge(v->zone2->region) == NULL &&
							v->zone2->region != r->zoneorig->region &&
							!interditretraite(v->zone2->region)) {
						/* voila une zone accessible en retraite */
						for (t = CENTRE.t; t < CENTRE.t + CENTRE.n; t++)
							if (t->region == v->zone2->region)
								break;
						if (t < CENTRE.t + CENTRE.n) { /* retraite possible sur un centre */
							retraitecentrepossible = TRUE;
							r = DELOGEE.t + DELOGEE.n; /* sortie de boucle */
							break;/* sortie de boucle */
						}
						/* cherche une unite delogee d'un autre pays */
						for (x = DELOGEE.t; x < DELOGEE.t + DELOGEE.n; x++) {
							if (x->unite->pays == p)
								continue;
							/* peut elle retraiter au meme endroit ? */
							switch (x->unite->typeunite) {
							case ARMEE:
								for (vv = ARMEEVOISIN.t; vv < ARMEEVOISIN.t	+ ARMEEVOISIN.n; vv++)
									if (vv->zone1 == x->unite->zone	&&
										vv->zone2->region != x->zoneorig->region &&
										vv->zone2->region == v->zone2->region) { /* retraite possible en collision */
										collisionpossible = TRUE;
										x = DELOGEE.t + DELOGEE.n; /* sortie de boucle */ /* ajout a confirmer */
										v = ARMEEVOISIN.t + ARMEEVOISIN.n; /* sortie de boucle */
										r = DELOGEE.t + DELOGEE.n; /* sortie de boucle */
										break;/* sortie de boucle */
									}
								break;
							case FLOTTE:
								for (ww = FLOTTEVOISIN.t; ww < FLOTTEVOISIN.t
										+ FLOTTEVOISIN.n; ww++)
									if (ww->zone1 == x->unite->zone	&&
										ww->zone2->region != x->zoneorig->region &&
										ww->zone2->region == v->zone2->region) { /* retraite possible en collision */
										collisionpossible = TRUE;
										x = DELOGEE.t + DELOGEE.n; /* sortie de boucle */ /* ajout a confirmer */
										v = ARMEEVOISIN.t + ARMEEVOISIN.n; /* sortie de boucle */
										r = DELOGEE.t + DELOGEE.n; /* sortie de boucle */
										break;/* sortie de boucle */
									}
								break;
							}
						}
					}
				break;

			case FLOTTE:
				for (w = FLOTTEVOISIN.t; w < FLOTTEVOISIN.t + FLOTTEVOISIN.n; w++)
					if (w->zone1 == r->unite->zone &&
							/* marche aussi avec le fonction chercheoccupant() */
						chercheoccupantnondeloge(w->zone2->region) == NULL &&
						w->zone2->region != r->zoneorig->region &&
						!interditretraite(w->zone2->region)) {

						/* voila une zone accessible en retraite */
						for (t = CENTRE.t; t < CENTRE.t + CENTRE.n; t++)
							if (t->region == w->zone2->region)
								break;
						if (t < CENTRE.t + CENTRE.n) { /* retraite possible sur un centre */
							retraitecentrepossible = TRUE;
							r = DELOGEE.t + DELOGEE.n; /* sortie de boucle */
							break;/* sortie de boucle */
						}
						/* cherche une unite delogee d'un autre pays */
						for (x = DELOGEE.t; x < DELOGEE.t + DELOGEE.n; x++) {
							if (x->unite->pays == p)
								continue;
							/* peut elle retraiter au meme endroit ? */
							switch (x->unite->typeunite) {
							case ARMEE:
								for (vv = ARMEEVOISIN.t; vv < ARMEEVOISIN.t	+ ARMEEVOISIN.n; vv++)
									if (vv->zone1 == x->unite->zone	&&
										vv->zone2->region != x->zoneorig->region &&
										vv->zone2->region == w->zone2->region) { /* retraite possible en collision */
										collisionpossible = TRUE;
										x = DELOGEE.t + DELOGEE.n; /* sortie de boucle */ /* ajout a confirmer */
										w = FLOTTEVOISIN.t + FLOTTEVOISIN.n; /* sortie de boucle */
										r = DELOGEE.t + DELOGEE.n; /* sortie de boucle */
										break;/* sortie de boucle */
									}
								break;
							case FLOTTE:
								for (ww = FLOTTEVOISIN.t; ww < FLOTTEVOISIN.t + FLOTTEVOISIN.n; ww++)
									if (ww->zone1 == x->unite->zone	&&
										ww->zone2->region != x->zoneorig->region &&
										ww->zone2->region == w->zone2->region) { /* retraite possible en collision */
										collisionpossible = TRUE;
										x = DELOGEE.t + DELOGEE.n; /* sortie de boucle */ /* ajout a confirmer */
										w = FLOTTEVOISIN.t + FLOTTEVOISIN.n; /* sortie de boucle */
										r = DELOGEE.t + DELOGEE.n; /* sortie de boucle */
										break;/* sortie de boucle */
									}
								break;
							}
						}
					}
				break;
			}
		}

		if (retraitecentrepossible || collisionpossible)
			continue; /* une delogee du pays peut retraiter sur un centre ou realiser une collision */

		/* test presume inutile a confirmer */
		/*if (q < UNITE.t + UNITE.n)
			continue; *//* pays suivant */

		/* si on arrive ici c'est que le pays est mort */

		if (strcmp(NOMPROGRAMME, "JOUEUR")) { /* ne pas afficher si appel du joueur */
			if (OPTIONw) {
				cherchechaine(__FILE__, 45, buf, 1, p->nom); /*"Suppression des unites du pays %1"*/
				informer(buf);
			}
		}

		for (r = DELOGEE.t; r < DELOGEE.t + DELOGEE.n; r++) {

			if (r->unite->pays != p)
				continue;

			/* la marque comme aneantie */
			ANEANTIE.t[ANEANTIE.n].delogee = r;
			ANEANTIE.n++;
			assert(ANEANTIE.n <= NANEANTIES);
		}

	} /* pays */
}
/**************************************************************************/

static _DECISION_UNIT *cherchedecision1(_DECISION *decision, _MOUVEMENT *mouv) {
	_DECISION_UNIT *p;

	for (p = decision->DECISION1.t; p < decision->DECISION1.t
			+ decision->DECISION1.n; p++)
		if (p->mouvement == mouv)
			return p;

	assert(FALSE);
	return NULL; /* evite un avertissement */
}

static _DECISION_TWO_UNIT *cherchedecision2(_DECISION *decision,
		_MOUVEMENT *mouv1, _MOUVEMENT *mouv2) {
	return &decision->DECISION2.t[mouv1 - MOUVEMENT.t][mouv2 - MOUVEMENT.t];
}

static _DECISION_REGION *cherchedecision3(_DECISION *decision, _REGION *reg) {
	_DECISION_REGION *p;

	for (p = decision->DECISION3.t; p < decision->DECISION3.t
			+ decision->DECISION3.n; p++)
		if (p->region == reg)
			return p;

	assert(FALSE);
	return NULL; /* evite un avertissement */
}

static BOOL headtohead(_MOUVEMENT *mouv1, _MOUVEMENT *mouv2)
/* Renvoie TRUE si sont susceptible de se combattre (chacune veut aller a la place de l'autre */
{
	if (mouv1->typemouvement != ATTAQUE)
		return FALSE;

	if (mouv2->typemouvement != ATTAQUE)
		return FALSE;

	if (mouv1->zonedest->region != mouv2->unite->zone->region)
		return FALSE;

	if (mouv2->zonedest->region != mouv1->unite->zone->region)
		return FALSE;

	return TRUE;
}

static BOOL valid_convoy(_DECISION *decision, _ZONE *zone1, _ZONE *zone2,
		BOOL sur)
/* Le convoi existe si des flotte bien placees ont recu l'ordre adequat,
 de plus on trouve un chemin avec celles
 - si sur : sures de ne pas etre delogees,
 - sinon : pas sures d'etre delogees  */
{
	_UNITE *p, **s;
	_MOUVEMENT *q;
	_ZONE *zone;
	_CHAINE LACHAINE;
	BOOL ordredonne, bon_status;
	_DECISION_UNIT *r;

	LACHAINE.n = 0;
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
			r = cherchedecision1(decision, q);
			bon_status = (sur && r->dislodge == SUSTAINS) || (!sur
					&& (r->dislodge == SUSTAINS || r->dislodge
							== DISLODGE_UNDECIDED));
			if (!(ordredonne && bon_status)) {
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
			if (!flottevoisin(p->zone, zone2) && !contactconvoi(p->zone, zone2)) {
				LACHAINE.t[LACHAINE.n++] = p;
				zone = p->zone;
				p = UNITE.t;
				continue;
			}
			return TRUE;
		}

		if (LACHAINE.n != 0) {
			p = LACHAINE.t[--LACHAINE.n] + 1;
			if (LACHAINE.n == 0)
				zone = zone1;
			else
				zone = (LACHAINE.t[LACHAINE.n])->zone;
			continue;
		}
		return FALSE;
	}
}

/* -----------------------------------------------------------------------*/

/* Mon deplacement est-il accorde ? */
static BOOL move_decision(_DECISION *decision, _DECISION_UNIT *du) {
	_MOUVEMENT *p;
	_DECISION_UNIT *r;
	_DECISION_REGION *s;
	_DECISION_TWO_UNIT *t;
	BOOL cond1, cond2, fight_sure, fight_perhaps;

	if (du->mouvement->typemouvement != ATTAQUE)
		return FALSE;

	if (du->move != MOVE_UNDECIDED)
		return FALSE;

	/* Cas de succes du mouvement (deux conditions) */

	cond1 = TRUE;
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		if (headtohead(p, du->mouvement))
			break;
	fight_perhaps = FALSE;
	if (p < MOUVEMENT.t + MOUVEMENT.n) {
		t = cherchedecision2(decision, p, du->mouvement);
		fight_perhaps = (t->head_to_head_battle == FIGHT
				|| t->head_to_head_battle == FIGHT_UNDECIDED);
	}
	if (fight_perhaps) {
		r = cherchedecision1(decision, p);
		if (!(du->attack_strength_min > r->defend_strength_max))
			cond1 = FALSE;
	} else {
		s = cherchedecision3(decision, du->mouvement->zonedest->region);
		if (!(du->attack_strength_min > s->hold_strength_max))
			cond1 = FALSE;
	}

	cond2 = TRUE;
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

		if (p == du->mouvement)
			continue;

		if (p->typemouvement != ATTAQUE)
			continue;

		if (p->zonedest->region != du->mouvement->zonedest->region)
			continue;

		r = cherchedecision1(decision, p);
		if (!(du->attack_strength_min > r->prevent_strength_max)) {
			cond2 = FALSE;
			break;
		}
	}

	if (cond1 && cond2) {
		du->move = MOVES;
		return TRUE;
	}

	/* Cas d'echec du mouvement */

	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		if (headtohead(p, du->mouvement))
			break;
	fight_sure = FALSE;
	if (p < MOUVEMENT.t + MOUVEMENT.n) {
		t = cherchedecision2(decision, p, du->mouvement);
		fight_sure = (t->head_to_head_battle == FIGHT);
	}
	if (fight_sure) {
		r = cherchedecision1(decision, p);
		if (du->attack_strength_max <= r->defend_strength_min) {
			du->move = FAILS;
			return TRUE;
		}
	} else {
		s = cherchedecision3(decision, du->mouvement->zonedest->region);
		if (du->attack_strength_max <= s->hold_strength_min) {
			du->move = FAILS;
			return TRUE;
		}
	}

	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

		if (p->typemouvement != ATTAQUE)
			continue;

		if (p == du->mouvement)
			continue;

		if (p->zonedest->region != du->mouvement->zonedest->region)
			continue;

		r = cherchedecision1(decision, p);
		if (du->attack_strength_max <= r->prevent_strength_min) {
			du->move = FAILS;
			return TRUE;
		}
	}

	return FALSE;
}

/* Mon soutien est-il accorde ? */
static BOOL support_decision(_DECISION *decision, _DECISION_UNIT *du) {
	_MOUVEMENT *p;
	_DECISION_UNIT *r;
	BOOL possibly_attacked, sure_attacked;

	if (du->mouvement->typemouvement != SOUTIENOFF
			&& du->mouvement->typemouvement != SOUTIENDEF)
		return FALSE;

	if (du->support != SUPPORT_UNDECIDED)
		return FALSE;

	/* Raffinement par rapport a l'original : des delogees peuvent soutenir exceptionnellement */
	if (du->dislodge == DISLODGED && du->paradox == NO_PARADOX) {
		du->support = CUT;
		return TRUE;
	}

	possibly_attacked = sure_attacked = FALSE;
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

		if (p->typemouvement != ATTAQUE)
			continue;

		if (p->zonedest->region != du->mouvement->unite->zone->region)
			continue;

		if (du->mouvement->typemouvement == SOUTIENOFF
				&& du->mouvement->zonedest->region == p->unite->zone->region)
			continue;

		r = cherchedecision1(decision, p);
		if (r->attack_strength_min > 0) {
			possibly_attacked = sure_attacked = TRUE;
			break;
		}
		if (r->attack_strength_max > 0)
			possibly_attacked = TRUE;
	}

	if (sure_attacked) {
		du->support = CUT;
		return TRUE;
	}

	if (!possibly_attacked && du->dislodge == SUSTAINS) {
		du->support = GIVEN;
		return TRUE;
	}

	return FALSE;
}

/* Suis - je delogee ? */
static BOOL dislodge_decision(_DECISION *decision, _DECISION_UNIT *du) {
	_MOUVEMENT *p;
	_DECISION_UNIT *r;
	BOOL sure_attacked, possibly_attacked;

	if (du->dislodge != DISLODGE_UNDECIDED)
		return FALSE;

	if (du->mouvement->typemouvement == ATTAQUE && du->move == MOVES) {
		du->dislodge = SUSTAINS;
		return TRUE;
	}

	sure_attacked = possibly_attacked = FALSE;
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

		if (p->typemouvement != ATTAQUE)
			continue;

		if (p->zonedest->region != du->mouvement->unite->zone->region)
			continue;

		r = cherchedecision1(decision, p);
		switch (r->move) {
		case FAILS:
			break;
		case MOVES:
			possibly_attacked = sure_attacked = TRUE;
			p = MOUVEMENT.t + MOUVEMENT.n;
			break;
		case MOVE_UNDECIDED:
			possibly_attacked = TRUE;
			break;
		}
	}

	if (sure_attacked && ((du->mouvement->typemouvement == ATTAQUE && du->move
			== FAILS) || du->mouvement->typemouvement != ATTAQUE)) {
		du->dislodge = DISLODGED;
		return TRUE;
	}

	if (!possibly_attacked) {
		du->dislodge = SUSTAINS;
		return TRUE;
	}

	return FALSE;
}

/* Force pour realiser le mouvement souhaite */
static BOOL attack_strength_decision(_DECISION *decision, _DECISION_UNIT *du) {
	_MOUVEMENT *p;
	_UNITE *q;
	_DECISION_UNIT *r;
	_DECISION_TWO_UNIT *t;
	BOOL min_nul, victime_existe;
	_UNITE *victime[2];
	int prev_min, prev_max;
	enum {
		MIN_VALUE = 0, MAX_VALUE = 1
	} calculating;

	if (du->mouvement->typemouvement != ATTAQUE)
		return FALSE;

	if (du->attack_strength_min == du->attack_strength_max)
		return FALSE;

	prev_min = du->attack_strength_min;
	prev_max = du->attack_strength_max;

	min_nul = FALSE;
	switch (du->path) {
	case NO_PATH:
		du->attack_strength_min = du->attack_strength_max = 0;
		return TRUE;
	case PATH_UNDECIDED:
		du->attack_strength_min = 0;
		min_nul = TRUE;
		break;
	case PATH:
		break;
	}

	for (calculating = MIN_VALUE; calculating <= MAX_VALUE; calculating++) {

		/* Etape 1 : recherche de la victime du mouvement */

		victime[calculating] = NULL;

		for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
			if (headtohead(p, du->mouvement))
				break;

		victime_existe = FALSE;
		if (p < MOUVEMENT.t + MOUVEMENT.n) {
			t = cherchedecision2(decision, p, du->mouvement);
			victime_existe = (t->head_to_head_battle == FIGHT);
		}

		if (victime_existe)

			victime[calculating] = p->unite;

		else {

			if ((q = chercheoccupant(du->mouvement->zonedest->region)) != NULL) {

				for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
					if (p->unite == q)
						break;
				assert(p != MOUVEMENT.t + MOUVEMENT.n);

				if (p->typemouvement != ATTAQUE)
					victime[calculating] = q;
				else {
					r = cherchedecision1(decision, p);
					switch (r->move) {
					case FAILS:
						if (calculating == MIN_VALUE) {
							if (!min_nul)
								victime[calculating] = p->unite;
						} else
							victime[calculating] = p->unite;
						break;
					case MOVE_UNDECIDED:
						if (calculating == MIN_VALUE) {
							if (!min_nul)
								victime[calculating] = q;
						}
						break;
					case MOVES:
						break;
					}
				}
			}
		}

		/* Etape 2 : exploitation : on va compter les soutiens */

		if (victime[calculating] != NULL && victime[calculating]->pays
				== du->mouvement->unite->pays) {

			if (calculating == MIN_VALUE)
				du->attack_strength_min = 0;
			else
				du->attack_strength_max = 0;

		} else {

			if (calculating == MIN_VALUE) {
				if (!min_nul)
					du->attack_strength_min = 1;
			} else
				du->attack_strength_max = 1;

			for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

				if (p->typemouvement != SOUTIENOFF)
					continue;

				if (p->unitepass != du->mouvement->unite)
					continue;

				/* Les soutiens n'ont pas besoin de correspondre en cote */
				if (p->zonedest->region != du->mouvement->zonedest->region)
					continue;

				if (victime[calculating] != NULL && p->unite->pays
						== victime[calculating]->pays)
					continue;

				r = cherchedecision1(decision, p);
				switch (r->support) {
				case GIVEN:
					if (calculating == MIN_VALUE) {
						if (!min_nul)
							du->attack_strength_min++;
					} else
						du->attack_strength_max++;
					break;
				case CUT:
					break;
				case SUPPORT_UNDECIDED:
					if (calculating == MAX_VALUE)
						du->attack_strength_max++;
					break;
				}
			}
		}
	}

	return du->attack_strength_min != prev_min || du->attack_strength_max
			!= prev_max;
}

/* Force a vaincre pour aller a un endroit quelconque */
static BOOL hold_strength_decision(_DECISION *decision, _DECISION_REGION *du) {
	_UNITE *p;
	_MOUVEMENT *q, *s;
	_DECISION_UNIT *r;
	int prev_min, prev_max;

	if (du->hold_strength_min == du->hold_strength_max)
		return FALSE;

	if ((p = chercheoccupant(du->region)) == NULL) {
		du->hold_strength_min = du->hold_strength_max = 0;
		return FALSE;
	}

	prev_min = du->hold_strength_min;
	prev_max = du->hold_strength_max;

	for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
		if (q->unite == p)
			break;
	assert(q != MOUVEMENT.t + MOUVEMENT.n);

	if (q->typemouvement != ATTAQUE) {

		du->hold_strength_min = du->hold_strength_max = 1;

		for (s = MOUVEMENT.t; s < MOUVEMENT.t + MOUVEMENT.n; s++) {

			if (s->typemouvement != SOUTIENDEF)
				continue;

			if (s->unitepass != p)
				continue;

			r = cherchedecision1(decision, s);
			switch (r->support) {
			case GIVEN:
				du->hold_strength_min++;
				du->hold_strength_max++;
				break;
			case SUPPORT_UNDECIDED:
				du->hold_strength_max++;
				break;
			case FAILS:
				break;
			}
		}

	} else {

		r = cherchedecision1(decision, q);
		switch (r->move) {
		case MOVES:
			du->hold_strength_min = du->hold_strength_max = 0;
			break;
		case MOVE_UNDECIDED:
			du->hold_strength_min = 0;
			du->hold_strength_max = 1;
			break;
		case FAILS:
			du->hold_strength_min = du->hold_strength_max = 1;
			break;
		}

	}

	return du->hold_strength_min != prev_min || du->hold_strength_max
			!= prev_max;
}

/* Force d'empecher un mouvement vers la destination de son propre mouvement */
static BOOL prevent_strength_decision(_DECISION *decision, _DECISION_UNIT *du) {
	BOOL min_nul;
	_MOUVEMENT *p;
	_DECISION_UNIT *r;
	_DECISION_TWO_UNIT *t;
	int prev_min, prev_max;

	if (du->mouvement->typemouvement != ATTAQUE)
		return FALSE;

	if (du->prevent_strength_min == du->prevent_strength_max)
		return FALSE;

	prev_min = du->prevent_strength_min;
	prev_max = du->prevent_strength_max;

	min_nul = FALSE;
	switch (du->path) {
	case NO_PATH:
		du->prevent_strength_min = du->prevent_strength_max = 0;
		return TRUE;
	case PATH_UNDECIDED:
		du->prevent_strength_min = 0;
		min_nul = TRUE;
		break;
	case PATH:
		break;
	}

	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		if (headtohead(p, du->mouvement))
			break;
	if (p < MOUVEMENT.t + MOUVEMENT.n) {
		t = cherchedecision2(decision, p, du->mouvement);
		if (t->head_to_head_battle == FIGHT) {
			r = cherchedecision1(decision, p);
			switch (r->move) {
			case MOVES:
				du->prevent_strength_min = du->prevent_strength_max = 0;
				return TRUE;
			case MOVE_UNDECIDED:
				du->prevent_strength_min = 0;
				min_nul = TRUE;
				break;
			case FAILS:
				break;
			}
		}
	}

	if (!min_nul)
		du->prevent_strength_min = 1;
	du->prevent_strength_max = 1;
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

		if (p->typemouvement != SOUTIENOFF)
			continue;

		if (p->unitepass != du->mouvement->unite)
			continue;

		/* Les soutiens n'ont pas besoin de correspondre en cote */
		if (p->zonedest->region != du->mouvement->zonedest->region)
			continue;

		r = cherchedecision1(decision, p);
		switch (r->support) {
		case GIVEN:
			if (!min_nul)
				du->prevent_strength_min++;
			du->prevent_strength_max++;
			break;
		case CUT:
			break;
		case SUPPORT_UNDECIDED:
			du->prevent_strength_max++;
			break;
		}
	}

	return du->prevent_strength_min != prev_min || du->prevent_strength_max
			!= prev_max;
}

/* Force de s'opposer a un mouvement adverse */
static BOOL defend_strength_decision(_DECISION *decision, _DECISION_UNIT *du) {
	_MOUVEMENT *p;
	_DECISION_UNIT *q;
	int prev_min, prev_max;

	if (du->mouvement->typemouvement != ATTAQUE)
		return FALSE;

	if (du->defend_strength_min == du->defend_strength_max)
		return FALSE;

	prev_min = du->defend_strength_min;
	prev_max = du->defend_strength_max;

	du->defend_strength_min = du->defend_strength_max = 1;

	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

		if (p->typemouvement != SOUTIENOFF)
			continue;

		if (p->unitepass != du->mouvement->unite)
			continue;

		/* Les soutiens n'ont pas besoin de correspondre en cote */
		if (p->zonedest->region != du->mouvement->zonedest->region)
			continue;

		q = cherchedecision1(decision, p);
		switch (q->support) {
		case GIVEN:
			du->defend_strength_min++;
			du->defend_strength_max++;
			break;
		case SUPPORT_UNDECIDED:
			du->defend_strength_max++;
			break;
		case CUT:
			break;
		}
	}

	return du->defend_strength_min != prev_min || du->defend_strength_max
			!= prev_max;
}

/* Peut - on acceder a la destination du mouvement  */
static BOOL path_decision(_DECISION *decision, _DECISION_UNIT *du) {
	decision = decision; /* evite un avertissement */

	if (du->mouvement->typemouvement != ATTAQUE)
		return FALSE;

	if (du->path != PATH_UNDECIDED)
		return FALSE;

	switch (du->mouvement->unite->typeunite) {

	case FLOTTE:

		if (flottevoisin(du->mouvement->unite->zone, du->mouvement->zonedest)) {
			du->path = PATH;
			return TRUE;
		}

		break;

	case ARMEE:

		if (armeevoisin(du->mouvement->unite->zone, du->mouvement->zonedest)) {
			du->path = PATH;
			return TRUE;
		}

		switch (du->convoy_path) {
		case NO_CONVOY_PATH:
			du->path = NO_PATH;
			return TRUE;
		case CONVOY_PATH:
			du->path = PATH;
			return TRUE;
		case CONVOY_PATH_UNDECIDED:
			break;
		}

		break;
	}

	return FALSE;
}

/* Decision optionnelle dans l'algorithme DATC officiel */
/* Les deux unites vont - elle combattre ? */
static BOOL head_to_head_battle_decision(_DECISION *decision,
		_DECISION_UNIT *du1, _DECISION_UNIT *du2) {
	if (du1->mouvement->typemouvement != ATTAQUE
			|| du2->mouvement->typemouvement != ATTAQUE)
		return FALSE;

	if (!headtohead(du1->mouvement, du2->mouvement))
		return FALSE;

	if (decision->DECISION2.t[du1->mouvement - MOUVEMENT.t][du2->mouvement
			- MOUVEMENT.t].head_to_head_battle != FIGHT_UNDECIDED)
		return FALSE;

	if (du1->convoy_path == NO_CONVOY_PATH && du2->convoy_path
			== NO_CONVOY_PATH) {
		decision->DECISION2.t[du1->mouvement - MOUVEMENT.t][du2->mouvement
				- MOUVEMENT.t].head_to_head_battle = FIGHT;
		return TRUE;
	}

	/* DEBUT Specificite JEUX DESCARTES absente de DATC : voie terrestre en priorite */

	if (du2->convoy_path == NO_CONVOY_PATH) {
		if (du1->attack_strength_min > du2->defend_strength_max) {
			decision->DECISION2.t[du1->mouvement - MOUVEMENT.t][du2->mouvement
					- MOUVEMENT.t].head_to_head_battle = FIGHT;
			return TRUE;
		}
		if (du1->attack_strength_max <= du2->defend_strength_min) {
			decision->DECISION2.t[du1->mouvement - MOUVEMENT.t][du2->mouvement
					- MOUVEMENT.t].head_to_head_battle = NO_FIGHT;
			return TRUE;
		}
	}

	if (du1->convoy_path == NO_CONVOY_PATH) {
		if (du2->attack_strength_min > du1->defend_strength_max) {
			decision->DECISION2.t[du1->mouvement - MOUVEMENT.t][du2->mouvement
					- MOUVEMENT.t].head_to_head_battle = FIGHT;
			return TRUE;
		}
		if (du2->attack_strength_max <= du1->defend_strength_min) {
			decision->DECISION2.t[du1->mouvement - MOUVEMENT.t][du2->mouvement
					- MOUVEMENT.t].head_to_head_battle = NO_FIGHT;
			return TRUE;
		}
	}

	/* FIN  Specificite JEUX DESCARTES  */

	if (du1->convoy_path == CONVOY_PATH && du2->convoy_path == CONVOY_PATH) {
		decision->DECISION2.t[du1->mouvement - MOUVEMENT.t][du2->mouvement
				- MOUVEMENT.t].head_to_head_battle = NO_FIGHT;
		return TRUE;
	}

	return FALSE;
}

/* Decision optionnelle dans l'algorithme DATC officiel */
/* Peut - on acceder a la destination du mouvement par nu convoi ? */
static BOOL convoy_path_decision(_DECISION *decision, _DECISION_UNIT *du) {
	if (du->mouvement->typemouvement != ATTAQUE)
		return FALSE;

	if (du->convoy_path != CONVOY_PATH_UNDECIDED)
		return FALSE;

	if (du->mouvement->unite->typeunite != ARMEE) {
		du->convoy_path = NO_CONVOY_PATH;
		return TRUE;
	}

	if (valid_convoy(decision, du->mouvement->unite->zone,
			du->mouvement->zonedest, TRUE)) {
		du->convoy_path = CONVOY_PATH;
		return TRUE;
	}

	if (!valid_convoy(decision, du->mouvement->unite->zone,
			du->mouvement->zonedest, FALSE)) {
		du->convoy_path = NO_CONVOY_PATH;
		return TRUE;
	}

	return FALSE;
}

/* Decision completement ajoutee a l'algorithme DATC officiel */
/* Est - on une flotte cible d'un convoi et soutenant pour ou contre une flotte convoyeuse ? */
static BOOL paradox_decision(_DECISION *decision, _DECISION_UNIT *du)
/* A ce niveau la seule decision qui puisse etre prise et NO_PARADOX */
{
	_MOUVEMENT *p;
	_DECISION_UNIT *s;
	BOOL possible_attack_by_convoy;

	decision = decision; /* evite un avertissement compilateur */

	if (du->mouvement->typemouvement != SOUTIENDEF
			&& du->mouvement->typemouvement != SOUTIENOFF)
		return FALSE;

	if (du->paradox != PARADOX_UNDECIDED)
		return FALSE;

	if (du->mouvement->unite->typeunite != FLOTTE) {
		du->paradox = NO_PARADOX;
		return TRUE;
	}

	if (du->mouvement->unitepass->typeunite != FLOTTE) {
		du->paradox = NO_PARADOX;
		return TRUE;
	}

	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		if (p->unite == du->mouvement->unitepass)
			break;
	assert(p < MOUVEMENT.t + MOUVEMENT.n);
	if (p->typemouvement != CONVOI) {
		du->paradox = NO_PARADOX;
		return TRUE;
	}

	possible_attack_by_convoy = FALSE;
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {

		if (p->typemouvement != ATTAQUE)
			continue;

		if (p->zonedest->region != du->mouvement->unite->zone->region)
			continue;

		if (p->unite->typeunite != ARMEE)
			continue;

		if (armeevoisin(p->unite->zone, p->zonedest))
			continue;

		s = cherchedecision1(decision, p);
		if (s->convoy_path != NO_CONVOY_PATH)
			possible_attack_by_convoy = TRUE;
	}

	if (!possible_attack_by_convoy) {
		du->paradox = NO_PARADOX;
		return TRUE;
	}

	return FALSE;
}

static void init_decisions(_DECISION *decision) {
	_MOUVEMENT *p, *q;
	_REGION *r;

	decision->DECISION1.n = 0;
	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {
		decision->DECISION1.t[decision->DECISION1.n].move = MOVE_UNDECIDED;
		decision->DECISION1.t[decision->DECISION1.n].support
				= SUPPORT_UNDECIDED;
		decision->DECISION1.t[decision->DECISION1.n].dislodge
				= DISLODGE_UNDECIDED;
		decision->DECISION1.t[decision->DECISION1.n].attack_strength_min = 0;
		decision->DECISION1.t[decision->DECISION1.n].attack_strength_max
				= INFINITE;
		decision->DECISION1.t[decision->DECISION1.n].prevent_strength_min = 0;
		decision->DECISION1.t[decision->DECISION1.n].prevent_strength_max
				= INFINITE;
		decision->DECISION1.t[decision->DECISION1.n].defend_strength_min = 0;
		decision->DECISION1.t[decision->DECISION1.n].defend_strength_max
				= INFINITE;
		decision->DECISION1.t[decision->DECISION1.n].path = PATH_UNDECIDED;
		decision->DECISION1.t[decision->DECISION1.n].convoy_path
				= CONVOY_PATH_UNDECIDED;
		decision->DECISION1.t[decision->DECISION1.n].paradox
				= PARADOX_UNDECIDED;
		decision->DECISION1.t[decision->DECISION1.n].mouvement = p;
		decision->DECISION1.n++;
	}

	for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
		for (q = MOUVEMENT.t; q < MOUVEMENT.t + MOUVEMENT.n; q++)
			decision->DECISION2.t[p - MOUVEMENT.t][q - MOUVEMENT.t].head_to_head_battle
					= FIGHT_UNDECIDED;

	decision->DECISION3.n = 0;
	for (r = REGION.t; r < REGION.t + REGION.n; r++) {
		decision->DECISION3.t[decision->DECISION3.n].hold_strength_min = 0;
		decision->DECISION3.t[decision->DECISION3.n].hold_strength_max
				= INFINITE;
		decision->DECISION3.t[decision->DECISION3.n].region = r;
		decision->DECISION3.n++;
	}

}

/* Plutot pour la mise au point, appellee par assert_decisions_made() qui ne sert que de garde-fou */
static void decision_dump(_DECISION *decision) {
	_DECISION_UNIT *p;
	_DECISION_REGION *q;
	_MOUVEMENT *r, *s;

	(void) fprintf(stderr, "-----Decision dump ---------------\n");

	for (p = decision->DECISION1.t; p < decision->DECISION1.t
			+ decision->DECISION1.n; p++) {

		if (p->mouvement->typemouvement == ATTAQUE)
			switch (p->move) {
			case MOVES:
				(void) fprintf(stderr, "MOVES for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			case FAILS:
				(void) fprintf(stderr, "FAILS for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			default:
				(void) fprintf(stderr, "UNDECIDED_MOVE for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			}

		if (p->mouvement->typemouvement == SOUTIENDEF
				|| p->mouvement->typemouvement == SOUTIENOFF) {
			switch (p->support) {
			case GIVEN:
				(void) fprintf(stderr, "SUPPORT_GIVEN for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			case CUT:
				(void) fprintf(stderr, "SUPPORT_CUT for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			default:
				(void) fprintf(stderr, "UNDECIDED_SUPPORT for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			}
			switch (p->paradox) {
			case PARADOX:
				(void) fprintf(stderr, "PARADOX for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			case NO_PARADOX:
				(void) fprintf(stderr, "NO_PARADOX for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			default:
				(void) fprintf(stderr, "UNDECIDED_PARADOX for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			}
		}

		switch (p->dislodge) {
		case SUSTAINS:
			(void) fprintf(stderr, "SUSTAINS for %s\n",
					p->mouvement->unite->zone->region->nom);
			break;
		case DISLODGED:
			(void) fprintf(stderr, "DISLODGED for %s\n",
					p->mouvement->unite->zone->region->nom);
			break;
		default:
			(void) fprintf(stderr, "UNDECIDED_DISLODGED for %s\n",
					p->mouvement->unite->zone->region->nom);
			break;
		}

		if (p->mouvement->typemouvement == ATTAQUE)
			(void) fprintf(stderr, "ATTACK_STRENGTH for %s = %d/%d\n",
					p->mouvement->unite->zone->region->nom,
					p->attack_strength_min, p->attack_strength_max);

		if (p->mouvement->typemouvement == ATTAQUE)
			(void) fprintf(stderr, "PREVENT_STRENGTH for %s = %d/%d\n",
					p->mouvement->unite->zone->region->nom,
					p->prevent_strength_min, p->prevent_strength_max);

		if (p->mouvement->typemouvement == ATTAQUE)
			(void) fprintf(stderr, "DEFEND_STRENGTH for %s = %d/%d\n",
					p->mouvement->unite->zone->region->nom,
					p->defend_strength_min, p->defend_strength_max);

		if (p->mouvement->typemouvement == ATTAQUE)
			switch (p->path) {
			case PATH:
				(void) fprintf(stderr, "PATH for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			case NO_PATH:
				(void) fprintf(stderr, "NO_PATH for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			default:
				(void) fprintf(stderr, "UNDECIDED_PATH for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			}

		if (p->mouvement->typemouvement == ATTAQUE)
			switch (p->convoy_path) {
			case CONVOY_PATH:
				(void) fprintf(stderr, "CONVOY_PATH for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			case NO_CONVOY_PATH:
				(void) fprintf(stderr, "NO_CONVOY_PATH for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			default:
				(void) fprintf(stderr, "UNDECIDED_CONVOY_PATH for %s\n",
						p->mouvement->unite->zone->region->nom);
				break;
			}

	}

	for (r = MOUVEMENT.t; r < MOUVEMENT.t + MOUVEMENT.n; r++)
		for (s = MOUVEMENT.t; s < MOUVEMENT.t + MOUVEMENT.n; s++)
			if (headtohead(r, s))
				switch (decision->DECISION2.t[r - MOUVEMENT.t][s - MOUVEMENT.t].head_to_head_battle) {
				case FIGHT:
					(void) fprintf(stderr, "FIGHT for %s / %s\n",
							r->unite->zone->region->nom,
							s->unite->zone->region->nom);
					break;
				case NO_FIGHT:
					(void) fprintf(stderr, "NO_FIGHT for %s / %s\n",
							r->unite->zone->region->nom,
							s->unite->zone->region->nom);
					break;
				default:
					(void) fprintf(stderr, "UNDECIDED_FIGHT for %s / %s\n",
							r->unite->zone->region->nom,
							s->unite->zone->region->nom);
					break;
				}

	for (q = decision->DECISION3.t; q < decision->DECISION3.t
			+ decision->DECISION3.n; q++) {
		if (q->hold_strength_min != 0 || q->hold_strength_max != 0)
			(void) fprintf(stderr, "HOLD_STRENGTH for %s : %d/%d\n",
					q->region->nom, q->hold_strength_min, q->hold_strength_max);
	}

	(void) fprintf(stderr, "--------------------\n");
}

/* Uniquement par securite */
static void assert_decisions_made(_DECISION *decision) {
	_DECISION_UNIT *p;
	_DECISION_REGION *q;
	_MOUVEMENT *r, *s;
	BOOL manque_decision;

	manque_decision = FALSE;

	for (p = decision->DECISION1.t; p < decision->DECISION1.t
			+ decision->DECISION1.n; p++) {

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->move == MOVE_UNDECIDED) {
				(void) fprintf(stderr, "MOVE_UNDECIDED for %s\n",
						p->mouvement->unite->zone->region->nom);
				manque_decision = TRUE;
			}
		}

		if (p->mouvement->typemouvement == SOUTIENDEF
				|| p->mouvement->typemouvement == SOUTIENOFF) {
			if (p->support == SUPPORT_UNDECIDED) {
				(void) fprintf(stderr, "SUPPORT_UNDECIDED for %s\n",
						p->mouvement->unite->zone->region->nom);
				manque_decision = TRUE;
			}
			if (p->paradox == PARADOX_UNDECIDED) {
				(void) fprintf(stderr, "PARADOX_UNDECIDED for %s\n",
						p->mouvement->unite->zone->region->nom);
				manque_decision = TRUE;
			}
		}

		if (p->dislodge == DISLODGE_UNDECIDED) {
			(void) fprintf(stderr, "DISLODGE_UNDECIDED for %s\n",
					p->mouvement->unite->zone->region->nom);
			manque_decision = TRUE;
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->attack_strength_min != p->attack_strength_max) {
				(void) fprintf(stderr, "ATTACK_STRENGTH_not_fixed for %s\n",
						p->mouvement->unite->zone->region->nom);
				manque_decision = TRUE;
			}
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->prevent_strength_min != p->prevent_strength_max) {
				(void) fprintf(stderr, "PREVENT_STRENGTH_not_fixed for %s\n",
						p->mouvement->unite->zone->region->nom);
				manque_decision = TRUE;
			}
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->defend_strength_min != p->defend_strength_max) {
				(void) fprintf(stderr, "DEFEND_STRENGTH_not_fixed for %s\n",
						p->mouvement->unite->zone->region->nom);
				manque_decision = TRUE;
			}
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->path == PATH_UNDECIDED) {
				(void) fprintf(stderr, "PATH_UNDECIDED for %s\n",
						p->mouvement->unite->zone->region->nom);
				manque_decision = TRUE;
			}
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->convoy_path == CONVOY_PATH_UNDECIDED) {
				(void) fprintf(stderr, "CONVOY_PATH_UNDECIDED for %s\n",
						p->mouvement->unite->zone->region->nom);
				manque_decision = TRUE;
			}
		}

	}

	for (r = MOUVEMENT.t; r < MOUVEMENT.t + MOUVEMENT.n; r++)
		for (s = MOUVEMENT.t; s < MOUVEMENT.t + MOUVEMENT.n; s++)
			if (headtohead(r, s))
				if (decision->DECISION2.t[r - MOUVEMENT.t][s - MOUVEMENT.t].head_to_head_battle
						== FIGHT_UNDECIDED) {
					(void) fprintf(stderr, "FIGHT_UNDECIDED for %s / %s\n",
							r->unite->zone->region->nom,
							s->unite->zone->region->nom);
					manque_decision = TRUE;
				}

	for (q = decision->DECISION3.t; q < decision->DECISION3.t
			+ decision->DECISION3.n; q++) {
		if (q->hold_strength_min != q->hold_strength_max) {
			(void) fprintf(stderr, "HOLD_STRENGTH_not_fixed for %s\n",
					q->region->nom);
			manque_decision = TRUE;
		}
	}

	if (manque_decision)
		decision_dump(decision);

	assert(!manque_decision);
}

static BOOL all_decisions_made(_DECISION *decision) {
	_DECISION_UNIT *p;
	_DECISION_REGION *q;
	_MOUVEMENT *r, *s;

	for (p = decision->DECISION1.t; p < decision->DECISION1.t
			+ decision->DECISION1.n; p++) {

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->move == MOVE_UNDECIDED)
				return FALSE;
		}

		if (p->mouvement->typemouvement == SOUTIENDEF
				|| p->mouvement->typemouvement == SOUTIENOFF) {
			if (p->support == SUPPORT_UNDECIDED)
				return FALSE;
			if (p->paradox == PARADOX_UNDECIDED)
				return FALSE;
		}

		if (p->dislodge == DISLODGE_UNDECIDED)
			return FALSE;

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->attack_strength_min != p->attack_strength_max)
				return FALSE;
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->prevent_strength_min != p->prevent_strength_max)
				return FALSE;
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->defend_strength_min != p->defend_strength_max)
				return FALSE;
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->path == PATH_UNDECIDED)
				return FALSE;
		}

		if (p->mouvement->typemouvement == ATTAQUE) {
			if (p->convoy_path == CONVOY_PATH_UNDECIDED)
				return FALSE;
		}

	}

	for (r = MOUVEMENT.t; r < MOUVEMENT.t + MOUVEMENT.n; r++)
		for (s = MOUVEMENT.t; s < MOUVEMENT.t + MOUVEMENT.n; s++)
			if (headtohead(r, s))
				if (decision->DECISION2.t[r - MOUVEMENT.t][s - MOUVEMENT.t].head_to_head_battle
						== FIGHT_UNDECIDED)
					return FALSE;

	for (q = decision->DECISION3.t; q < decision->DECISION3.t
			+ decision->DECISION3.n; q++) {
		if (q->hold_strength_min != q->hold_strength_max)
			return FALSE;
	}

	return TRUE;
}

static BOOL solve_circular(_DECISION *decision) {
	_DECISION_UNIT *p;
	BOOL tabou[NUNITES];
	_REGION *reg;
	int i, j;

	struct {
		int n;
		_DECISION_UNIT *t[NUNITES];
	} stack;

	for (i = 0; i < NUNITES; i++)
		tabou[i] = FALSE;

	for (;;) { /* boucle recherche toutes les suites */

		stack.n = 0;
		reg = NULL;

		/* On cherche une suite d'unites qui se suivent */
		for (;;) {

			/* cherche la suivangte ou premiere */
			for (p = decision->DECISION1.t; p < decision->DECISION1.t
					+ decision->DECISION1.n; p++) {

				if (p->mouvement->typemouvement != ATTAQUE)
					continue;

				if (p->move != MOVE_UNDECIDED)
					continue;

				if (tabou[p - decision->DECISION1.t])
					continue;

				if (reg == NULL || p->mouvement->unite->zone->region == reg)
					break;

			}

			/* Rien trouve : cette suite ne pourra plus etre agrandie */
			if (p == decision->DECISION1.t + decision->DECISION1.n)
				break;

			for (i = 0; i < stack.n; i++) {
				if (stack.t[i] == p) {
					for (j = i; j < stack.n; j++)
						stack.t[j]->move = MOVES;
					return TRUE;
				}
			}

			/* On met dans la suite */
			stack.t[stack.n++] = p;
			reg = p->mouvement->zonedest->region;

		} /* recherche un cycle */

		/* On ne veut plus voir les elements de cette suite non circulaire */
		for (j = 0; j < stack.n; j++)
			tabou[stack.t[j] - decision->DECISION1.t] = TRUE;

		/* A - t - on fini ? */
		for (p = decision->DECISION1.t; p < decision->DECISION1.t
				+ decision->DECISION1.n; p++) {

			if (p->mouvement->typemouvement != ATTAQUE)
				continue;

			if (p->move != MOVE_UNDECIDED)
				continue;

			if (tabou[p - decision->DECISION1.t])
				continue;
		}

		/* On a fini s'il ne reste plus de mouvement indecis non deja vu (tabou) */
		if (p == decision->DECISION1.t + decision->DECISION1.n)
			break;

	} /* recherche tous cycles */

	return FALSE;
}

static void propagation(_DECISION *decision) {
	_DECISION_UNIT *s, *t;
	_DECISION_REGION *u;
	BOOL modif;

	/* Propagation "normale" transitivement fermee */
	for (;;) {

		modif = FALSE;
		for (s = decision->DECISION1.t; s < decision->DECISION1.t
				+ decision->DECISION1.n; s++) {
			if (move_decision(decision, s))
				modif = TRUE;
			if (support_decision(decision, s))
				modif = TRUE;
			if (dislodge_decision(decision, s))
				modif = TRUE;
			if (attack_strength_decision(decision, s))
				modif = TRUE;
		}

		for (u = decision->DECISION3.t; u < decision->DECISION3.t
				+ decision->DECISION3.n; u++) {
			if (hold_strength_decision(decision, u))
				modif = TRUE;
		}

		for (s = decision->DECISION1.t; s < decision->DECISION1.t
				+ decision->DECISION1.n; s++) {
			if (prevent_strength_decision(decision, s))
				modif = TRUE;
			if (defend_strength_decision(decision, s))
				modif = TRUE;
			if (path_decision(decision, s))
				modif = TRUE;
			if (convoy_path_decision(decision, s))
				modif = TRUE;
		}

		/* additional to DATC */
		for (s = decision->DECISION1.t; s < decision->DECISION1.t
				+ decision->DECISION1.n; s++) {
			for (t = decision->DECISION1.t; t < decision->DECISION1.t
					+ decision->DECISION1.n; t++) {
				if (head_to_head_battle_decision(decision, s, t))
					modif = TRUE;
			}
		}


		for (s = decision->DECISION1.t; s < decision->DECISION1.t
				+ decision->DECISION1.n; s++) {
			/* added to DATC */
			if (paradox_decision(decision, s))
				modif = TRUE;
		}

		if (modif)
			continue;

		/* Action minimum quand on est bloque */
		modif = solve_circular(decision);
		if (modif)
			continue;

		break;

	}

}

static void resolution_paradoxes1(_DECISION *decision)
/* Annule un convoi qui change quelque chose sur les flottes delogees ou pas */
{
	_DECISION_UNIT *s, *t, *u;
	_DECISION *conjecture = &CONJONCTURE_DE_TRAVAIL;
	int i;

	struct {
		int n;
		_DECISION_UNIT *t[NUNITES];
	} stack;

	stack.n = 0;
	for (s = decision->DECISION1.t; s < decision->DECISION1.t
			+ decision->DECISION1.n; s++) {

		if (s->mouvement->typemouvement != ATTAQUE)
			continue;

		if (s->path != PATH_UNDECIDED)
			continue;

		if (s->convoy_path != CONVOY_PATH_UNDECIDED)
			continue;

		*conjecture = *decision;

		for (t = conjecture->DECISION1.t; t < conjecture->DECISION1.t
				+ decision->DECISION1.n; t++)
			if (s->mouvement == t->mouvement)
				break;
		assert(t < conjecture->DECISION1.t + decision->DECISION1.n);
		t->convoy_path = NO_CONVOY_PATH;

		propagation(conjecture);

		for (u = decision->DECISION1.t, t = conjecture->DECISION1.t; u
				< decision->DECISION1.t + decision->DECISION1.n; u++, t++)
			if (t->dislodge != u->dislodge)
				stack.t[stack.n++] = s; /* On met dans la liste */

	}

	for (i = 0; i < stack.n; i++)
		stack.t[i]->convoy_path = NO_CONVOY_PATH;

}

static void resolution_paradoxes2(_DECISION *decision) {
	_DECISION_UNIT *s;
	int i;

	struct {
		int n;
		_DECISION_UNIT *t[NUNITES];
	} stack;

	stack.n = 0;
	for (s = decision->DECISION1.t; s < decision->DECISION1.t
			+ decision->DECISION1.n; s++) {

		if (s->mouvement->typemouvement != SOUTIENDEF
				&& s->mouvement->typemouvement != SOUTIENOFF)
			continue;

		if (s->paradox != PARADOX_UNDECIDED)
			continue;

		/* On met dans la liste */
		stack.t[stack.n++] = s;

	}

	for (i = 0; i < stack.n; i++)
		stack.t[i]->paradox = PARADOX;

}

int resoudmouvements(void) { /* Renvoie le nombre de phases */
	_MOUVEMENT *p;
	_DECISION_UNIT *s, *t;
	int passe;
	char buf[TAILLEMESSAGE];
	char bufn1[TAILLEENTIER];

	init_decisions(&DECISION_OFFICIELLE);

	passe = 0;

	for (;;) {

		passe++;
		assert(passe <= MAXPASSES);

		/* Propage les decisions et resoud les mouvement en cycle */
		propagation(&DECISION_OFFICIELLE);

		/* Invalide les convois qui ont une consequence sur le delogement des flottes */
		resolution_paradoxes1(&DECISION_OFFICIELLE);

		/* Marque les flottes peut etre en paradoxe comme en paradoxe */
		resolution_paradoxes2(&DECISION_OFFICIELLE);

		/* Condition d'arret : on sait tout ce qu'il y a a savoir */
		if (all_decisions_made(&DECISION_OFFICIELLE))
			break;

	}

	assert_decisions_made(&DECISION_OFFICIELLE);

	if (OPTIONw) {
		(void) sprintf(bufn1, "%d", passe);
		cherchechaine(__FILE__, 44, buf, 1, bufn1); /*"Fin de la resolution passe %1"*/
		informer(buf);
	}

	/* Exploitation des resultats */
	DELOGEE.n = 0;
	for (s = DECISION_OFFICIELLE.DECISION1.t; s
			< DECISION_OFFICIELLE.DECISION1.t + DECISION_OFFICIELLE.DECISION1.n; s++) {

		switch (s->mouvement->typemouvement) {
		case STAND:
			s->mouvement->valable = (s->dislodge == SUSTAINS);
			break;

		case ATTAQUE:
			s->mouvement->valable = (s->move == MOVES);
			break;

		case SOUTIENDEF:
			s->mouvement->valable = (s->support == GIVEN);
			s->mouvement->coupe = (s->support == CUT);
			for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
				if (p->unite == s->mouvement->unitepass)
					break;
			assert(p < MOUVEMENT.t + MOUVEMENT.n);
			s->mouvement->dedaigne = (p->typemouvement == ATTAQUE);
			s->mouvement->paradoxe = (s->paradox == PARADOX);
			break;

		case SOUTIENOFF:
			s->mouvement->valable = (s->support == GIVEN);
			s->mouvement->coupe = (s->support == CUT);
			for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
				if (p->unite == s->mouvement->unitepass)
					break;
			assert(p < MOUVEMENT.t + MOUVEMENT.n);
			s->mouvement->dedaigne = (p->typemouvement != ATTAQUE
					/* Les soutiens n'ont pas besoin de correspondre en cote */
					|| p->zonedest->region != s->mouvement->zonedest->region);
			s->mouvement->paradoxe = (s->paradox == PARADOX);
			break;

		case CONVOI:
			s->mouvement->valable = (s->dislodge == SUSTAINS);
			for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++)
				if (p->unite == s->mouvement->unitepass)
					break;
			assert(p < MOUVEMENT.t + MOUVEMENT.n);
			s->mouvement->dedaigne = (p->typemouvement != ATTAQUE
					|| p->zonedest != s->mouvement->zonedest);
			break;
		}

		if (s->dislodge == DISLODGED) {

			/* Trouve la delogeuse */
			for (p = MOUVEMENT.t; p < MOUVEMENT.t + MOUVEMENT.n; p++) {
				if (p->typemouvement != ATTAQUE)
					continue;
				if (p->zonedest->region != s->mouvement->unite->zone->region)
					continue;
				t = cherchedecision1(&DECISION_OFFICIELLE, p);
				if (t->move == MOVES)
					break;
			}
			assert(p < MOUVEMENT.t + MOUVEMENT.n);

			/* Inseree dans la liste des delogees */
			DELOGEE.t[DELOGEE.n].unite = s->mouvement->unite;
			DELOGEE.t[DELOGEE.n].uniteorig = p->unite;
			DELOGEE.t[DELOGEE.n].zoneorig = p->unite->zone;
			DELOGEE.n++;
			assert(DELOGEE.n <= NDELOGEES);

		}

	}

	return passe;

}
