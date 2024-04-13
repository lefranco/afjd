#!/usr/bin/env python3


"""
Reorder everythng after inserting a new regions...
Bewate : still need to do :
  - distancing
  - neighbourhood (by hand)
  - visibility
"""

import argparse
import typing
import os
import sys
import json


INSERT_POSITION = 5 # albania
INSERT_TYPE = 1 # coast


def reorder(json_variant_data: typing.Dict[str, typing.Any], json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ reorder """

    # -------
    # variant
    # -------

    # regions
    json_variant_data['regions'].insert(INSERT_POSITION - 1, INSERT_TYPE)

    # centers
    json_variant_data['centers'] = list(map(lambda n: n + 1 if n >= INSERT_POSITION else n, json_variant_data['centers']))  # type: ignore

    # coastal_zones
    json_variant_data['coastal_zones'] = list(map(lambda t: [t[0] + 1, t[1]] if t[0] >= INSERT_POSITION else t, json_variant_data['coastal_zones']))  # type: ignore

    # start_units
    json_variant_data['start_units'] = list(map(lambda d: {k: list(map(lambda n: n + 1 if n >= INSERT_POSITION else n, v)) for k, v in d.items()}, json_variant_data['start_units']))  # type: ignore

    # neighbouring
    json_variant_data['neighbouring'] = list(map(lambda d: {str(int(k) + 1) if int(k) >= INSERT_POSITION else k: list(map(lambda n: n + 1 if n >= INSERT_POSITION else n, v)) for k, v in d.items()}, json_variant_data['neighbouring']))  # type: ignore

    # ----------
    # parameters
    # ----------

    # zones
    json_parameters_data['zones'] = {str(int(k) + 1) if int(k) >= INSERT_POSITION else k: v for k, v in json_parameters_data['zones'].items()}

    # zone_areas
    json_parameters_data['zone_areas'] = {str(int(k) + 1) if int(k) >= INSERT_POSITION else k: v for k, v in json_parameters_data['zone_areas'].items()}


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--variant_file', required=True, help='Load variant json file')
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    args = parser.parse_args()

    #  load files at start
    variant_file = args.variant_file
    parameters_file = args.parameters_file

    if not os.path.exists(variant_file):
        print(f"File '{variant_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    if not os.path.exists(parameters_file):
        print(f"File '{parameters_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    # load variant data from json data file
    with open(variant_file, "r", encoding='utf-8') as read_file:
        try:
            json_variant_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {variant_file} : {exception}")
            sys.exit(-1)

    # load parameters from json data file
    with open(parameters_file, "r", encoding='utf-8') as read_file:
        try:
            json_parameters_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {parameters_file} : {exception}")
            sys.exit(-1)

    reorder(json_variant_data, json_parameters_data)

    output = json.dumps(json_variant_data, indent=4, ensure_ascii=False)
    with open(variant_file, "w", encoding='utf-8') as write_file:
        write_file.write(output)

    output = json.dumps(json_parameters_data, indent=4, ensure_ascii=False)
    with open(parameters_file, "w", encoding='utf-8') as write_file:
        write_file.write(output)


if __name__ == "__main__":
    main()
