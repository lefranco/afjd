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
    parser.add_argument('-i', '--input_file', required=True, help='Input and output json file')
    parser.add_argument('-s', '--scale', required=True, type=float, help='scale')
    args = parser.parse_args()

    json_input = args.input_file
    scale = args.scale
    json_output = json_input

    # load parameters from json data file
    with open(json_input, "r", encoding='utf-8') as read_file:
        try:
            json_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {json_input} : {exception}")
            sys.exit(-1)

    for zone_data in json_data['zones'].values():

        zone_data["x_pos"] = round(zone_data["x_pos"] * scale)
        zone_data["x_legend_pos"]  = round(zone_data["x_legend_pos"] * scale)
        zone_data["y_pos"] = round(zone_data["y_pos"] * scale)
        zone_data["y_legend_pos"] = round(zone_data["y_legend_pos"] * scale)

    for center_data in json_data['centers'].values():

        center_data["x_pos"] = round(center_data["x_pos"] * scale)
        center_data["y_pos"] = round(center_data["y_pos"] * scale)

    for zone_areas_data in json_data['zone_areas'].values():
        zone_areas_data['area'] = [[round(x*scale), round(y*scale)] for x,y in zone_areas_data['area']]

    map_data = json_data["map"]
    map_data["width"] = round(map_data["width"] * scale)
    map_data["height"] = round(map_data["height"] * scale)

    output = json.dumps(json_data, indent=4, ensure_ascii=False)
    with open(json_output, 'w', encoding='utf-8') as file_ptr:
        file_ptr.write(output)

    print(f"Modified file copied to {json_output}")


if __name__ == '__main__':
    main()
