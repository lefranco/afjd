#!/usr/bin/env python3


"""
Make background color
"""

import argparse
import typing
import os
import sys
import json


INSERT_POSITION = 5 # albania
INSERT_TYPE = 1 # coast


def background(json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ background """

    # ----------
    # parameters
    # ----------

    # roles
    for role, role_data in json_parameters_data['roles'].items():
        if int(role) == 0:
            continue
        for color in ('red', 'green', 'blue'):
            unit_color = role_data[color][0]
            role_data[color][1] = unit_color - 10 if unit_color > 127 else unit_color + 10


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    args = parser.parse_args()

    #  load files at start
    parameters_file = args.parameters_file

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

    background(json_parameters_data)

    output = json.dumps(json_parameters_data, indent=4, ensure_ascii=False)
    with open(parameters_file, "w", encoding='utf-8') as write_file:
        write_file.write(output)


if __name__ == "__main__":
    main()
