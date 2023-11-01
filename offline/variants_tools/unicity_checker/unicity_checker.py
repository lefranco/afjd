#!/usr/bin/env python3


"""
Checks unicity of trigrams
"""

import argparse
import json
import sys


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', required=True, help='Input  json file')
    args = parser.parse_args()

    json_input = args.input_file

    # load parameters from json data file
    with open(json_input, "r", encoding='utf-8') as read_file:
        try:
            json_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {json_input} : {exception}")
            sys.exit(-1)

    names_set = set()
    for zone_data in json_data['zones'].values():

        name = zone_data["name"]
        if name and name in names_set:
            print(f"Name '{name}' is duplicated")
            sys.exit(-1)

        names_set.add(name)


if __name__ == '__main__':
    main()
