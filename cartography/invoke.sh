#!/bin/bash

./parse.py \
   -m ../client-ihms-brython/variants/standard/diplomania/map.png \
   -v ../rest-servers/games/variants/standard.json \
   -p ../client-ihms-brython/variants/standard/diplomania/parameters.json \
   -s ./input/Carte_annotee.svg \
   -F new_parameters.json \
   -S dummy.json

exit
