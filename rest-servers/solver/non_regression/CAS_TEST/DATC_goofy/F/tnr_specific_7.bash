#!/usr/bin/bash

#analyse parametres
lexique=hasbro
carte=HASBRO
pref=07

#verification preliminaire
if ! test -r "$pref.TXT" ; then 	
	echo Fichier $pref.TXT introuvable
	exit 255
fi

# -----------------------------------------------------
# Verifie que le resultat d'une invocation de SOLVEUR
# est restee conforme a celui attendu
# -----------------------------------------------------
#enleve les commentaires
sed 's/;.*$//' $pref.TXT > $pref.TXT2

rm -f $pref.ORD
if ! traducteur $pref.TXT2 $pref.ORD "${DIPLOCOM}/traduction/lexique_$lexique.txt" "${DIPLOCOM}/traduction/filtre.txt"  ; then
	echo Probleme traducteur
    exit 255
fi
rm $pref.TXT2

rm -f $pref.DAT
aideur -c $carte -s -S A01  -o $pref.ORD -i $pref.DAT 
if ! aideur -c $carte -s -S A01  -o $pref.ORD -i $pref.DAT 2>/dev/null ; then
	echo Probleme aideur
    exit 255
fi

rm -f $pref.TM1
rm -f $pref.TM2

if solveur -en -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3  2>$pref.TM2 ; then
    if diff $pref.TM3 $pref.RES 1>/dev/null 2>/dev/null ; then
		  retour=0
    else
		  retour=1
    fi
else
	retour=1
fi

rm -f $pref.ORD
rm -f $pref.TM1
rm -f $pref.TM2
rm -f $pref.TM3

exit $retour
