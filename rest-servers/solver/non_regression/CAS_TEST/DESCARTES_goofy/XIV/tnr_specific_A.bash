#!/usr/bin/bash

lexique=descartes
carte=DESCARTES

# -----------------------------------------------------
# Verifie que le resultat d'une invocation de SOLVEUR
# est restee conforme a celui attendu
# -----------------------------------------------------
for pref in PRI ETE AUT HIV ; do
	#enleve les commentaires
	sed 's/;.*$//' $pref.TXT > $pref.TXT2

	rm -f $pref.ORD
	if ! traducteur $pref.TXT2 $pref.ORD "${DIPLOCOM}/traduction/lexique_$lexique.txt" "${DIPLOCOM}/traduction/filtre.txt"  ; then
		echo Probleme traducteur
    	exit 255
	fi
	rm $pref.TXT2
done

pref=PRI
rm -f $pref.DAT
if ! aideur -c $carte -s -S P01  -o $pref.ORD -i $pref.DAT 2>/dev/null ; then
	echo Probleme aideur
    exit 255
fi

pref=PRI
prefs=ETE
if solveur -c $carte -s -o $pref.ORD -i $pref.DAT -f $prefs.DAT 2>/dev/null ; then
	pref=ETE
	prefs=AUT
	if solveur -c $carte -s -o $pref.ORD -i $pref.DAT -f $prefs.DAT  2>/dev/null ; then
		pref=AUT
		prefs=HIV
		if solveur -c $carte -s -o $pref.ORD -i $pref.DAT -f $prefs.DAT  2>/dev/null ; then
			pref=HIV
			prefs=BIL
			if solveur -c $carte -s -o $pref.ORD -i $pref.DAT -f $prefs.DAT  2>/dev/null ; then

			    if diff $prefs.RES $prefs.DAT 1>/dev/null 2>/dev/null ; then
					 retour=0
			    else
					 retour=1
          fi
                
		  else
				retour=1
		  fi
		else
			retour=1
		fi
	else
		retour=1
	fi
else
	retour=1
fi

##rm -f $pref.TM1

exit $retour
