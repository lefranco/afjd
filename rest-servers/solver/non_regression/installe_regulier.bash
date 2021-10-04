#!/usr/bin/bash

# pour trouver les fichiers
export DIPLOCOM=/cygdrive/c/diplocom

# pour executer les programmes
PATH=$PATH:${DIPLOCOM}/programmes/

#analyse parametres
entree2=$4
entree=$3
rep=$2
cas=$1
pref=$rep/$cas

# mode d'emploi
if test "$1" = "" ; then
	echo $0 \<cas\> \<repertoire\> \<fichier texte ordres mouvements\> [ \<fichier texte ordres retraites\> ]
	exit 0
fi

echo Installation de repertoire $rep cas $cas

#verification preliminaire
if ! test -r "$entree" ; then 	
	echo Fichier $entree existe pas
    exit 255
fi
if test -r "$pref.TXT" ; then 	
	echo Fichier $pref.TXT existe deja donc remplace
fi

cp $entree  $pref.TXT 1>/dev/null 2>/dev/null 

# -----------------------------------------------------
# Installe le resultat d'une invocation de SOLVEUR
# -----------------------------------------------------
#enleve les commentaires
sed 's/;.*$//' $pref.TXT > $pref.TXT2

rm -f $pref.ORD
if ! traducteur.exe $pref.TXT2 $pref.ORD ${DIPLOCOM}/traduction/lexique_hasbro.txt ${DIPLOCOM}/traduction/filtre.txt  ; then
	echo Probleme traducteur 1
    exit 255
fi
rm $pref.TXT2

rm -f $pref.DAT
if ! aideur.exe -s -S P01  -o $pref.ORD -i $pref.DAT ; then # 2>/dev/null  ; then
	echo Probleme aideur 
    exit 255
fi

# si retraites 
if test -r "$entree2" ; then 	

	echo avec retraites

	cp $entree2  $pref.RET 1>/dev/null 2>/dev/null 
    
	if ! solveur.exe -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3 2>/dev/null ; then
		echo Probleme solveur premiere invocation
    	exit 255    
	fi
    rm -f $pref.TM1    
    
	cp $pref.TM3 $pref.DAT >/dev/null 2>/dev/null

	#enleve les commentaires
	sed 's/;.*$//' $pref.RET > $pref.RET2

	rm -f $pref.ORD
	if ! traducteur.exe $pref.RET2 $pref.ORD ${DIPLOCOM}/traduction/lexique_hasbro.txt ${DIPLOCOM}/traduction/filtre.txt  ; then
		echo Probleme traducteur 2
    	exit 255
	fi
	rm $pref.RET2

fi

rm -f $pref.TM1
rm -f $pref.TM2
echo "====================================="
cat $pref.TXT
echo "====================================="
if solveur.exe -s -o $pref.ORD -i $pref.DAT -a $pref.TM1  2>$pref.TM2 ; then
    cp $pref.TM1 $pref.RES 1>/dev/null 2>/dev/null 
	rm -f $pref.ERR
    echo NE PRODUIT PAS D\'ERREUR
    cat $pref.RES
else
    cp $pref.TM2 $pref.ERR 1>/dev/null 2>/dev/null 
	rm -f $pref.RES
    echo PRODUIT UNE ERREUR
    cat $pref.ERR
fi

rm -f $pref.TM1
rm -f $pref.TM2
rm -f $pref.TM3
##rm -f $pref.ORD
rm -f $pref.DAT

exit 0
