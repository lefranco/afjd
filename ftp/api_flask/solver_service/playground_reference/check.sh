#!/usr/bin/bash

# to find files
export DIPLOCOM=$(pwd)/DIPLOCOM

# to execute programs
export PATH=$PATH:$(pwd)/bin


solveur -c DEFAULT -o ./ORDRES.ORD -i ./SITUATION.DAT -f RESULTAT.DAT

if [ $? -eq 0 ] ; then
    echo "Result:"
    cat RESULTAT.DAT
    rm RESULTAT.DAT
fi
