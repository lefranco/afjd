#!/usr/bin/bash

lexique=hasbro
carte=HASBRO
pref=03

# -----------------------------------------------------
# Verifie que le resultat d'une invocation de SOLVEUR
# est restee conforme a celui attendu
# -----------------------------------------------------

rm -f $pref.TM1

if ! solveur -en -c $carte -s -PR $pref.TM1 -i $pref.DAT 2>$pref.TM2  ; then
	retour=1
else
    if diff $pref.TM1 $pref.RES 1>/dev/null 2>/dev/null ; then
		retour=0
    else
		retour=1
    fi
fi

rm -f $pref.TM2
rm -f $pref.ORD

exit $retour
