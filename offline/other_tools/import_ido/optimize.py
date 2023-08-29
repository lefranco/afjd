#!/usr/bin/env python3


"""
optimize parameter file
shift positions to avoid them to be too close
"""

import typing
import argparse
import json
import itertools
import math
import sys

SCALING_X = 5.
SCALING_Y = 5.
MAX_DIST = 25

TRACE = False


class Point:
    """ Point """

    def __init__(self, x: int, y: int) -> None:  # pylint: disable=invalid-name
        self.x = x  # pylint: disable=invalid-name
        self.y = y  # pylint: disable=invalid-name

    def distance(self, other: 'Point') -> float:
        """ distance """
        return math.sqrt((other.x - self.x)**2 + (other.y - self.y)**2)

    def __str__(self) -> str:
        return f"x={self.x} y={self.y}"


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_input', required=True, help='Input parameters json file')
    parser.add_argument('-F', '--first_format_json_output', required=True, help='Output optimized parameters json file')
    args = parser.parse_args()

    json_parameters_input = args.parameters_input
    first_format_json_output = args.first_format_json_output

    # load parameters from json data file
    with open(json_parameters_input, "r", encoding='utf-8') as read_file:
        json_parameters_data = json.load(read_file)

    # ============= optim ===============

    items: typing.Dict[Point, typing.Any] = {}

    for zone in json_parameters_data['zones'].values():

        # ignore specific coasts
        if not zone['name']:
            continue

        x_pos = zone['x_pos']
        y_pos = zone['y_pos']
        point = Point(x_pos, y_pos)
        items[point] = zone

    while True:

        smallest_dist = sys.float_info.max
        for point1, point2 in itertools.combinations(items.keys(), 2):
            dist = point1.distance(point2)
            if dist < smallest_dist:
                couple = (point1, point2)
                smallest_dist = dist

        if smallest_dist > MAX_DIST:
            break

        (point1, point2) = couple
        zone1 = items[point1]
        zone2 = items[point2]
        if TRACE:
            print(f"Pushing aside {zone1['name']} and {zone2['name']} distant of {smallest_dist}")

        # push them aside
        point1.x += round((point1.x - point2.x) / SCALING_X)
        point1.y += round((point1.y - point2.y) / SCALING_Y)
        point2.x += round((point2.x - point1.x) / SCALING_X)
        point2.y += round((point2.y - point1.y) / SCALING_Y)

    # ============= output ===============

    for point, element in items.items():

        delta_x = element['x_legend_pos'] - element['x_pos']
        element['x_pos'] = point.x
        element['x_legend_pos'] = element['x_pos'] + delta_x

        delta_y = element['y_legend_pos'] - element['y_pos']
        element['y_pos'] = point.y
        element['y_legend_pos'] = element['y_pos'] + delta_y

    output = json.dumps(json_parameters_data, indent=4, ensure_ascii=False)
    with open(first_format_json_output, 'w', encoding='utf-8') as file_ptr:
        file_ptr.write(output)


if __name__ == '__main__':
    main()
