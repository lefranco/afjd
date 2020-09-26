/* UTILS.C **********************************************************/

char *Strlwr(char *);
char *Strupr(char *);

/* ERREURS.C **********************************************************/

int vpays(_PAYS *);
void impromptu(const char *);
void initialisetablesaisons(void);
void initialisetableerreur(void);
void informer(const char *);
void avertir(const char *);
void erreurverif(_PAYS *, TYPEERREURVERIF, const char *);
void erreurverif2(_PAYS *, TYPEERREURVERIF, const char *);
void erreurparse(_PAYS *, TYPEERREURPARSE, BOOL, const char *);
void erreur(_PAYS *, TYPEERREUR, const char *);

/* LANGUE.C **********************************************************/

void addpath(char *, const char *, BOOL);
void cherchechaine(const char *, const int, char *, int, ...);

/* CONVOIS.C ********************************************************/

BOOL contactconvoi(_ZONE *, _ZONE *);
BOOL convoinecessaire(_MOUVEMENT *);
BOOL convoipossible(_UNITE *, _ZONE *, _ZONE *);
BOOL convoiexiste(_ZONE *, _ZONE *);
BOOL convoivalide(_ZONE *, _ZONE *);
BOOL empecheconvoi(_UNITE *, _ZONE *, _ZONE *);
_UNITE *unitedupaysempechantconvoi(_PAYS *, _ZONE *, _ZONE *);
BOOL peutconvoyer(_UNITE *, _UNITE *, _ZONE *);

/* GESTION.C ********************************************************/

void lesajustements(_PAYS *, int *, int *, int *);
BOOL compatibles(TYPEUNITE, _ZONE *);
_PAYS *paysdinitiale(int);
_PAYS *cherchepays(char *);
_PAYS *chercheadjectifpays(char *);
_REGION *chercheregion(char *);
_CENTRE *cherchecentre(char *);
_CENTREDEPART *cherchecentredepart(char *);
_ZONE *cherchezone(char *);
BOOL cotesexistent(_ZONE *zone);
_UNITE *chercheunite(char *);
_UNITE *chercheuniteavecpays(char *);
_DELOGEE *cherchedelogee(char *);
_UNITE *chercheoccupant(_REGION *);
_UNITE *chercheoccupantnondeloge(_REGION *);
BOOL flottevoisin(_ZONE *, _ZONE *);
BOOL armeevoisin(_ZONE *, _ZONE *);
int eloignement(TYPEUNITE, _ZONE *, _PAYS *);
BOOL contactsoutienflotte(_ZONE *, _ZONE *);
BOOL contactsoutienarmee(_ZONE *, _ZONE *);
BOOL centrepossede(_CENTRE *);
BOOL possede(_PAYS *, _CENTRE *);
BOOL interditretraite(_REGION *);
BOOL uniteaneantie(_UNITE *);
BOOL unitedelogee(_UNITE *);
void initialisetablevoisinages(void);

/* PARSE.C **********************************************************/

/* Ici parce que utilisees par le module ploteur */
void readtoken(char *, TOKEN *);
void ungettoken(TOKEN *);
void gettoken(FILE *, TOKEN *);

void parsecarte(char *);
void parsesituation(char *);
void parsemouvements(char *);
void parseretraites(char *);
void parseajustements(char *);

/* RESOUD.C *********************************************************/

void creemouvements(_PAYS *);
void creeretraites(_PAYS *);
void creeajustements(_PAYS *);
void verifmouvements(void);
void verifretraites(void);
void verifajustements(void);
int resoudmouvements(void);
void modifmouvements(void);
void modifretraites(void);
void modifajustements(void);
void dupliquepossessions(void);
void modifpossessions(void);
void calculedisparitions(void);
void suppressionelimines(void);
void finretraites(void);
void calculaneanties(void);
void calculinterdites(void);
void suppressionelimines2(void);

/* HEURIS.C *********************************************************/
void calculeeloignements(void);
void verifiecarte(void);

/* DECRIT.C *********************************************************/

/* pour la mise au point */
#ifdef DEBUG
void decritcarte(void);
#endif

/* operationnel */
/* pour le ploteur aussi */
void classementpays(void);
void calculajustements(_PAYS *, int *, int *, int *);
/* reste */
void decritsituation(char *);
void decritordres(char *, BOOL);
void decritprototypes(char *, _PAYS *);
void decritordressecurite(char *, _PAYS *);
void decritordrescomplets(char *, _PAYS *, BOOL);
void decritactifs(char *);
void decritvivants(char *);

/* SOLVEUR.C *********************************************************/
