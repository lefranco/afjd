#!/usr/bin/env python3


"""
Shifts all position of same delta
"""

import argparse
import json
import sys


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', required=True, help='Input  json file')
    parser.add_argument('-x', '--x_shift', required=True, type=int, help='x_shift')
    parser.add_argument('-y', '--y_shift', required=True, type=int, help='y_shift')
    args = parser.parse_args()

    json_input = args.input_file
    x_shift = args.x_shift
    y_shift = args.y_shift
    json_output = f"{json_input}.shifted"

    # load parameters from json data file
    with open(json_input, "r", encoding='utf-8') as read_file:
        try:
            json_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {json_input} : {exception}")
            sys.exit(-1)

    for zone_data in json_data['zones'].values():

        zone_data["x_pos"] += x_shift
        zone_data["x_legend_pos"] += x_shift
        zone_data["y_pos"] += y_shift
        zone_data["y_legend_pos"] += y_shift

    for center_data in json_data['centers'].values():

        center_data["x_pos"] += x_shift
        center_data["y_pos"] += y_shift

    for zone_areas_data in json_data['zone_areas'].values():
        zone_areas_data['area'] = [[x+x_shift, y+y_shift] for x,y in zone_areas_data['area']]



    output = json.dumps(json_data, indent=4, ensure_ascii=False)
    with open(json_output, 'w', encoding='utf-8') as file_ptr:
        file_ptr.write(output)

    print(f"Modified file copied to {json_output}")


if __name__ == '__main__':
    main()
