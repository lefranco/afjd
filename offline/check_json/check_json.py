#!/usr/bin/env python3


"""
File : check_json.py

parses to check json files
"""

import argparse
import json
import sys


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--variant_input', required=True, help='Input variant json file')
    parser.add_argument('-p', '--parameters_input', required=True, help='Input parameters (names) json file')
    args = parser.parse_args()

    json_variant_input = args.variant_input
    json_parameters_input = args.parameters_input

    json_variant_output = f"{json_variant_input}.clean"
    json_parameters_output = f"{json_parameters_input}.clean"

    # load variant from json data file
    with open(json_variant_input, "r", encoding='utf-8') as read_file:
        try:
            json_variant_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {json_variant_input} : {exception}")
            sys.exit(-1)

    # load parameters from json data file
    with open(json_parameters_input, "r", encoding='utf-8') as read_file:
        try:
            json_parameters_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {json_parameters_input} : {exception}")
            sys.exit(-1)


if __name__ == '__main__':
    main()
