#define EOS 		'\0'

#define TAILLEMESSAGE   300
#define TAILLENOMFIC    150
#define TAILLEMOT       100
#define TAILLEENTIER    15

#define MAXPASSES       10
#define BLOCAGE			3      /* en annees */

#define NPAYSS          8
#define NREGIONS        100
#define NCENTRES        50
#define NCENTREDEPARTS  30
#define NZONES          100
#define NARMEEVOISINS   300
#define NFLOTTEVOISINS  300

#define NUNITES         50
#define NUNITEFUTURES   25
#define NPOSSESSIONS    50

#define NMOUVEMENTS     50
#define NRETRAITES      20
#define NAJUSTEMENTS    20

#define NINTERDITS      10
#define NDELOGEES       10
#define NANEANTIES      10

#define NDISPARITIONS 	NPAYSS
#define NELOIGNEMENTS   1500

#define INF(a,b) ((a) < (b) ? (a) : (b))

#define LISTE(type,max)	struct  {int  n; type t[max]; }
#define LISTE2(type,max)	struct  {type t[max][max]; }

#define NSAISONS 		5
#define MAXIMUMANNEE	99

/* pas connus hors DOS */

