#!/usr/bin/bash

# pour trouver les fichiers
export DIPLOCOM=$(pwd)/DIPLOCOM

# pour executer les programmes
export PATH=$PATH:$(pwd)/bin


solveur -c DEFAULT -o ./ORDRES.ORD -i ./SITUATION.DAT -f RESULTAT.DAT

echo "Resultat:"
cat RESULTAT.DAT

