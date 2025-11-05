#define EOS 		'\0'

#define TAILLEMESSAGE   300
#define TAILLENOMFIC    200
#define TAILLEMOT       100
#define TAILLEENTIER    15

#define MAXPASSES       10
#define BLOCAGE			3      /* en annees */

#define NPAYSS          50
#define NREGIONS        200
#define NCENTRES        100
#define NCENTREDEPARTS  60
#define NZONES          250
#define NARMEEVOISINS   1000
#define NFLOTTEVOISINS  1000

#define NUNITES         100
#define NUNITEFUTURES   50
#define NPOSSESSIONS    100

#define NMOUVEMENTS     100
#define NRETRAITES      50
#define NAJUSTEMENTS    50

#define NINTERDITS      20
#define NDELOGEES       20
#define NANEANTIES      20

#define NCOTESPOSSS     10

#define NDISPARITIONS 	NPAYSS
#define NELOIGNEMENTS   6000

#define INF(a,b) ((a) < (b) ? (a) : (b))

#define LISTE(type,max)	struct  {int  n; type t[max]; }
#define LISTE2(type,max)	struct  {type t[max][max]; }

#define NSAISONS 		5
#define MAXIMUMANNEE	99

/* pas connus hors DOS */

