#!/usr/bin/bash

lexique=hasbro
carte=HASBRO
pref=02

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

rm -f $pref.TM1

if solveur -en -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 2>$pref.TM2  ; then
	retour=1
else
    if diff $pref.TM2 $pref.ERR 1>/dev/null 2>/dev/null ; then
		retour=0
    else
		retour=1
    fi
fi

rm -f $pref.TM2
rm -f $pref.ORD

exit $retour
