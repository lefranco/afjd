#!/usr/bin/bash

lexique=descartes
carte=DESCARTES
pref=A

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


if solveur -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1  2>/dev/null ; then
    if diff $pref.TM1 $pref.RES 1>/dev/null 2>/dev/null ; then
		retour=0
    else
		retour=1
    fi
else
	retour=1
fi

rm -f $pref.TM1
rm -f $pref.ORD

exit $retour
