#!/usr/bin/bash

# pour trouver les fichiers
export DIPLOCOM=/cygdrive/c/diplocom

# pour executer les programmes
PATH=$PATH:$DIPLOCOM/programmes/

carte=HASBRO
pref=essai

aideur.exe -c $carte -s -o $pref.ORD  -i $pref.DAT
#gdb --args aideur.exe -c $carte -s -o $pref.ORD  -i $pref.DAT
cat $pref.DAT
