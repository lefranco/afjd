#!/usr/bin/env python3


"""
Try to guess neighbourhood
"""

import typing
import argparse
import os
import sys
import json
import itertools
import math


TOLERANCE = 10

class Point(typing.NamedTuple):
    x_pos: int
    y_pos: int


class Segment(typing.NamedTuple):
    edge1: Point
    edge2: Point


class Zones:
    """ Zone """

    nomenclature: typing.Dict[int, 'Zones'] = {}

    def __init__(self, number: int, name: str):
        self._number = number
        self._name = name
        self._region_type:typing.Optional[int] = None
        self._polygon: typing.Optional[typing.List[Segment]] = None
        Zones.nomenclature[number] = self

    def put_region_type(self, region_type: int) -> None:
        """ put_region_type """
        self._region_type = region_type

    def put_polygon(self, polygon: typing.List[typing.List[int]]) -> None:
        """ put_polygon """
        self._polygon = [Segment(Point(*p1), Point(*p2)) for p1, p2 in itertools.pairwise(polygon)]

    @property
    def region_type(self) -> typing.Optional[int]:
        """ region_type """
        return self._region_type

    @property
    def polygon(self) -> typing.Optional[typing.List[Segment]]:
        """ polygon """
        return self._polygon

    def __str__(self) -> str:
        return f"{self._name}"

# region type
# 1 = COAST
# 2 = LAND
# 3 = SEA


def find_neighbourhood(json_variant_data: typing.Dict[str, typing.Any], json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ find_neighbourhood """

    def compatibles(region_type1: int, region_type2: int) -> bool:
        """ compatibles """
        if 1 in {region_type1, region_type2}:
            return True
        return region_type1 == region_type2

    def adjacent(polygon1: typing.List[Segment], polygon2: typing.List[Segment]) -> bool:
        """ adjacent """

        def close_points(point1: Point, point2: Point) -> bool:
            """ close_points """
            return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) < TOLERANCE

        def close_segments(segment1: Segment, segment2: Segment) -> bool:
            """ close_segments """
            return (close_points(segment1[0], segment2[0]) and close_points(segment1[1], segment2[1])) or (close_points(segment1[0], segment2[1]) and close_points(segment1[1], segment2[0]))

        return any(close_segments(s1, s2) for s1, s2 in itertools.product(polygon1, polygon2))

    # create zone
    for num_zone_str, zone_data in json_parameters_data['zones'].items():
        zone = Zones(int(num_zone_str), zone_data['full_name'])

    # put type from variant
    for num, region_type in enumerate(json_variant_data['regions']):
        num_zone = num + 1
        zone = Zones.nomenclature[num_zone]
        zone.put_region_type(region_type)

    # put poly from parameters
    for num_zone_str, zone_area_data in json_parameters_data['zone_areas'].items():

        polygon = zone_area_data['area']

        num_zone = int(num_zone_str)
        zone = Zones.nomenclature[num_zone]
        zone.put_polygon(polygon)

    for zone1, zone2 in itertools.combinations(Zones.nomenclature.values(), 2):
        assert zone1.region_type is not None
        assert zone2.region_type is not None
        if not compatibles(zone1.region_type, zone2.region_type):
            continue
        assert zone1.polygon is not None
        assert zone2.polygon is not None
        if not adjacent(zone1.polygon, zone2.polygon):
            continue
        print(f"Seems {zone1} neighbour to {zone2}")


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

    # load parameters from json data file
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

    find_neighbourhood(json_variant_data, json_parameters_data)


if __name__ == "__main__":
    main()
