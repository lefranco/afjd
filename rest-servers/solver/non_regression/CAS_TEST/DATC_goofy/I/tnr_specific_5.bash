#!/usr/bin/bash

lexique=hasbro
carte=HASBRO
pref=5

# -----------------------------------------------------
# Verifie que le resultat d'une invocation de SOLVEUR
# est restee conforme a celui attendu
# -----------------------------------------------------
#printemps
#enleve les commentaires
sed 's/;.*$//' $pref.PRI > $pref.TXT2

rm -f $pref.ORD
if ! traducteur $pref.TXT2 $pref.ORD "${DIPLOCOM}/traduction/lexique_$lexique.txt" "${DIPLOCOM}/traduction/filtre.txt"  ; then
	echo Probleme traducteur
    exit 255
fi
rm $pref.TXT2

rm -f $pref.DAT
if ! aideur -c $carte -s -S P01  -o $pref.ORD -i $pref.DAT 2>/dev/null ; then
	echo Probleme aideur
    exit 255
fi

if ! solveur -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3 2>$pref.TM2  ; then
	echo Probleme solveur
    exit 255
fi

cp $pref.TM3 $pref.DAT >/dev/null 2>/dev/null

rm -f $pref.ORD
touch $pref.ORD
#ete
if ! solveur -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3 2>$pref.TM2  ; then
	echo Probleme solveur
    exit 255
fi

cp $pref.TM3 $pref.DAT >/dev/null 2>/dev/null

#automne
#enleve les commentaires
sed 's/;.*$//' $pref.AUT > $pref.TXT2

rm -f $pref.ORD
if ! traducteur $pref.TXT2 $pref.ORD "${DIPLOCOM}/traduction/lexique_$lexique.txt" "${DIPLOCOM}/traduction/filtre.txt"  ; then
	echo Probleme traducteur
    exit 255
fi
rm $pref.TXT2

if ! solveur -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3 2>$pref.TM2  ; then
	echo Probleme solveur 
    exit 255
fi

cp $pref.TM3 $pref.DAT >/dev/null 2>/dev/null

rm -f $pref.ORD
touch $pref.ORD
#hiver
if ! solveur -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3 2>$pref.TM2  ; then
	echo Probleme solveur 
    exit 255
fi

cp $pref.TM3 $pref.DAT >/dev/null 2>/dev/null

#bilan
#enleve les commentaires
sed 's/;.*$//' $pref.TXT > $pref.TXT2

rm -f $pref.ORD
if ! traducteur $pref.TXT2 $pref.ORD "${DIPLOCOM}/traduction/lexique_$lexique.txt" "${DIPLOCOM}/traduction/filtre.txt"  ; then
	echo Probleme traducteur
    exit 255
fi
rm $pref.TXT2

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
