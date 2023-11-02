#!/usr/bin/env python3


"""
Build nomenclature
"""

import argparse
import json
import sys
import os
import typing


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--parameters_file', required=True, help='Input json file')
    parser.add_argument('-o', '--output_file', required=True, help='Output ezml file')
    args = parser.parse_args()

    #  load files at start
    parameters_file = args.parameters_file
    output_file = args.output_file

    if not os.path.exists(parameters_file):
        print(f"File '{parameters_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    # load parameters from json data file
    with open(parameters_file, "r", encoding='utf-8') as read_file:
        try:
            json_parameters_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {parameters_file} : {exception}")
            sys.exit(-1)

    # to check unity
    names_set = set()

    # to output nomenclatura
    abbr2name: typing.Dict[str, str] = {}

    for zone_data in json_parameters_data['zones'].values():

        name = zone_data["name"]
        if not name:
            continue

        if name in names_set:
            print(f"Name '{name}' is duplicated", file=sys.stderr)
            sys.exit(-1)

        names_set.add(name)

        full_name = zone_data["full_name"]
        abbr2name[name] = full_name

    # create and save nomenclature
    with open(output_file, 'w', encoding='utf-8') as write_file:

        write_file.write("$ Nomenclature\n")
        write_file.write("\n")
        write_file.write("= Régions et abbréviations de la variante\n")
        write_file.write("| Abbréviation | Nom complet |\n")
        for name, full_name in sorted(abbr2name.items(), key=lambda t: t[0]):
            write_file.write(f"| {name} | {full_name} |\n")
        write_file.write("=\n")
        write_file.write("\n")


if __name__ == '__main__':
    main()
