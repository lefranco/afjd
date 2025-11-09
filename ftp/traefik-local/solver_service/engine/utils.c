#include <ctype.h>
extern char *Strupr(char *string);
extern char *Strlwr(char *string);

char *Strupr(char *string)
{
 char *s;
 if (string)
 {
for (s = string; *s; ++s)
 *s = (char) toupper((int) *s);
 }
 return string;
} 
char *Strlwr(char *string)
{
 char *s;
 if (string)
 {
for (s = string; *s; ++s)
 *s = (char) tolower((int) *s);
 }
 return string;
}
