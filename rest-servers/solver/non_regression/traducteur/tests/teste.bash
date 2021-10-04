#!/usr/bin/bash

# pour trouver les fichiers
export DIPLOCOM=/cygdrive/c/diplocom

# pour executer les programmes
PATH=$PATH:$DIPLOCOM/programmes/


traducteur.exe entree.txt sortie.txt "/cygdrive/c/diplocom/traduction/lexique_hasbro.txt" "/cygdrive/c/diplocom/traduction/filtre.txt"

cat sortie.txt
