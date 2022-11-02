#!/usr/bin/bash

# pour trouver les fichiers
export DIPLOCOM=$(pwd)/DIPLOCOM

# pour executer les programmes
export PATH=$PATH:$(pwd)/bin

echo $PATH

	lexique=descartes
	carte=DESCARTES

pref=MOVES

traducteur $pref.TXT2 $pref.ORD "${DIPLOCOM}/traduction/lexique_$lexique.txt" "${DIPLOCOM}/traduction/filtre.txt" 

rm -f $pref.DAT

aideur -c $carte -s -S P01  -o $pref.ORD -i $pref.DAT_ 

sed 's/SAISON PRINTEMPS/SAISON AUTOMNE/' $pref.DAT_ > $pref.DAT


solveur -c $carte -s -o $pref.ORD -i $pref.DAT -a $pref.TM1 -f $pref.TM3 

