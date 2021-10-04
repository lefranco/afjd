#!/usr/bin/bash


#analyse parametres
lexique=hasbro
carte=HASBRO
if test "$3" == "D" ; then
	lexique=descartes
	carte=DESCARTES
fi
rep=$2
cas=$1
pref=$rep/$cas

# mode d'emploi
if test "$1" = "" ; then
	echo $0 \<cas\> \<repertoire\> [ D \(si Descartes\) ]
	exit 0
fi

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
if ! aideur -c $carte -s -S P01  -o $pref.ORD -i $pref.DAT 2>/dev/null ; then
	echo Probleme aideur
	exit 255
fi

##rm -f $pref.TM1
##rm -f $pref.TM2

# il y a des retraites
if test -r "$pref.RET" ; then 	

	# ordres mouvement
	if ! solveur -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3 2>$pref.TM2 ; then
		retour=1
	fi

	# maj situation
	cp $pref.TM3 $pref.DAT >/dev/null 2>/dev/null

	#enleve les commentaires
	sed 's/;.*$//' $pref.RET > $pref.RET2

	rm -f $pref.ORD
	if ! traducteur $pref.RET2 $pref.ORD "${DIPLOCOM}/traduction/lexique_$lexique.txt" "${DIPLOCOM}/traduction/filtre.txt"  ; then
		echo Probleme traducteur 
		exit 255
	fi
	rm $pref.RET2

	rm -f $pref.TM1
	rm -f $pref.TM2

fi

# maintenant on regarde
if solveur -en -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3 2>$pref.TM2 ; then
	if diff $pref.TM1 $pref.RES 1>/dev/null 2>/dev/null ; then
		retour=0
	else
		retour=1
	fi
else
	if diff $pref.TM2 $pref.ERR 1>/dev/null 2>/dev/null ; then
		retour=0
	else
		retour=1
    fi
fi

##rm -f $pref.TM1
##rm -f $pref.TM2
##rm -f $pref.TM3
##rm -f $pref.ORD
##rm -f $pref.DAT

exit $retour
