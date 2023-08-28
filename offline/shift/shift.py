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
    parser.add_argument('-i', '--input_file', required=True, help='Input  json file')
    args = parser.parse_args()

    json_input = args.input_file
    json_output = f"{json_input}.shifted"

    # load parameters from json data file
    with open(json_input, "r", encoding='utf-8') as read_file:
        try:
            json_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {json_input} : {exception}")
            sys.exit(-1)

    for zone_data in json_data['zones'].values():

        zone_data["y_pos"] += 6
        zone_data["y_legend_pos"] += 6

    output = json.dumps(json_data, indent=4)
    with open(json_output, 'w') as file_ptr:
        file_ptr.write(output)


if __name__ == '__main__':
    main()
