#!/bin/bash

echo "Parsing...."
./parse.py \
   -m ../client-ihms-brython/variants/standard/diplomania/map.png \
   -v ../rest-servers/games/variants/standard.json \
   -p ../client-ihms-brython/variants/standard/diplomania/parameters.json \
   -s ./input/Carte_annotee.svg \
   -F new_parameters.json

echo "Optimizing...."
./optimize.py \
   -p new_parameters.json \
   -F new_parameters_opt.json


exit
