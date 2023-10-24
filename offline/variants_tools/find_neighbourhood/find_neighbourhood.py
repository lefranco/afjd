#!/usr/bin/env python3


"""
Try to guess neighbourhood
"""

import typing
import multiprocessing
import argparse
import os
import sys
import json
import itertools
import collections
import math


# two segment with middle further than this are not considered to be potentially intersected
FAR_AWAY_OPTIMIZATION = 50.

# a segment shorter that this is not considered
SEGMENT_LENGTH_REQUIREMENT = 1.

# a point closer that this to a segment is in this segment
DISTANCE_POINT_IN_SEGMENT_TOLERANCE = 5.


class Point(typing.NamedTuple):
    """ Point """
    x_pos: int
    y_pos: int


class Segment(typing.NamedTuple):
    """ Segment """
    edge1: Point
    edge2: Point


class Zone:
    """ Zone """

    nomenclature: typing.Dict[int, 'Zone'] = {}

    def __init__(self, number: int, name: str):
        self._number = number
        self._name = name
        self._region_type: typing.Optional[int] = None
        self._polygon: typing.Optional[typing.List[Segment]] = None
        Zone.nomenclature[number] = self

    def put_region_type(self, region_type: int) -> None:
        """ put_region_type """
        self._region_type = region_type

    def put_polygon(self, polygon: typing.List[typing.List[int]]) -> None:
        """ put_polygon """
        #  self._polygon = [Segment(Point(*polygon[i]), Point(*polygon[i + 1])) for i in range(len(polygon) - 1)]
        self._polygon = [Segment(Point(*p1), Point(*p2)) for p1, p2 in itertools.pairwise(polygon)]

    @property
    def number(self) -> int:
        """ number """
        return self._number

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

# REMINDER

# region type
# 1 = COAST
# 2 = LAND
# 3 = SEA

# unit type
# 1 = ARMY
# 2 = FLEET


def find_neighbourhood(json_variant_data: typing.Dict[str, typing.Any], json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ find_neighbourhood """

    def compatible(unit_type: int, region_type: int) -> bool:
        """ compatible : reject zone of weong region_type """
        if unit_type == 1:
            return region_type in {1, 2}
        return region_type in {1, 3}

    def acceptable(unit_type: int, zone: Zone) -> bool:
        """ acceptable : reject cases of special coasts"""
        if zone.number in {c[0] for c in json_variant_data['coastal_zones']}:
            if unit_type == 2:
                return False
        elif zone.number > len(json_variant_data['regions']):
            if unit_type == 1:
                return False
        return True

    def adjacent(polygon1: typing.List[Segment], polygon2: typing.List[Segment]) -> bool:
        """ adjacent """

        def intersect_segments(segment1: Segment, segment2: Segment) -> bool:
            """ intersect_segments """

            def distance_point_point(point1: Point, point2: Point) -> float:
                """ distance_point_poiont """
                return math.sqrt((point2.x_pos - point1.x_pos)**2 + (point2.y_pos - point1.y_pos)**2)

            def middle_segment(segment: Segment) -> Point:
                """ length_segment """
                return Point((segment.edge1.x_pos + segment.edge2.x_pos) // 2, (segment.edge1.y_pos + segment.edge2.y_pos) // 2)

            def length_segment(segment: Segment) -> float:
                """ length_segment """
                return distance_point_point(segment.edge1, segment.edge2)

            def point_in_segment(point: Point, segment: Segment) -> bool:
                """ point_in_segment """

                def distance_point_segment(point: Point, segment: Segment) -> float:
                    """ distance_point_segment """

                    delta_x = segment.edge2.x_pos - segment.edge1.x_pos
                    delta_y = segment.edge2.y_pos - segment.edge1.y_pos

                    delta_px = point.x_pos - segment.edge1.x_pos
                    delta_py = point.y_pos - segment.edge1.y_pos

                    if delta_x == 0 and delta_y == 0:
                        return math.sqrt(delta_px**2 + delta_py**2)

                    ratio = (delta_px * delta_x + delta_py * delta_y) / (delta_x ** 2 + delta_y ** 2)

                    if ratio < 0:
                        closest = segment.edge1
                    elif ratio > 1:
                        closest = segment.edge2
                    else:
                        closest = Point(round(segment.edge1.x_pos + ratio * delta_x), round(segment.edge1.y_pos + ratio * delta_y))

                    return distance_point_point(point, closest)

                return distance_point_segment(point, segment) < DISTANCE_POINT_IN_SEGMENT_TOLERANCE

            # ignore short segments
            if length_segment(segment1) < SEGMENT_LENGTH_REQUIREMENT or length_segment(segment2) < SEGMENT_LENGTH_REQUIREMENT:
                return False

            # ignore far away segments
            mid_seg1 = middle_segment(segment1)
            mid_seg2 = middle_segment(segment2)
            if distance_point_point(mid_seg1, mid_seg2) > FAR_AWAY_OPTIMIZATION:
                return False

            # a segment is included in the other (2 posibilities)
            if point_in_segment(segment1.edge1, segment2) and point_in_segment(segment1.edge2, segment2):
                return True
            if point_in_segment(segment2.edge1, segment1) and point_in_segment(segment2.edge2, segment1):
                return True

            # the segments intersect (4 possibilities)
            if point_in_segment(segment1.edge1, segment2) and point_in_segment(segment2.edge1, segment1):
                return True
            if point_in_segment(segment1.edge1, segment2) and point_in_segment(segment2.edge2, segment1):
                return True
            if point_in_segment(segment1.edge2, segment2) and point_in_segment(segment2.edge1, segment1):
                return True
            if point_in_segment(segment1.edge2, segment2) and point_in_segment(segment2.edge2, segment1):
                return True

            return False

        return any(intersect_segments(s1, s2) for s1, s2 in itertools.product(polygon1, polygon2))

    def processed_evaluate(unit_type: int, result_queue: multiprocessing.Queue) -> None:  # type: ignore
        """ processed_evaluate """

        dict_unit_type: typing.Dict[str, typing.List[int]] = {}

        for zone1 in Zone.nomenclature.values():

            assert zone1.region_type is not None

            # fleet on sea or coast, army on fleet or land
            if not compatible(unit_type, zone1.region_type):
                continue

            # fleet sticks to special coats, army to the container
            if not acceptable(unit_type, zone1):
                continue

            print(f"  Finding neighbours by {'army' if unit_type == 1 else 'fleet'} of {zone1}({zone1.number}):")

            dict_unit_type[str(zone1.number)] = []
            assert zone1.polygon is not None

            for zone2 in Zone.nomenclature.values():

                if zone2 is zone1:
                    continue
                assert zone2.region_type is not None

                # fleet on sea or coast, army on fleet or land
                if not compatible(unit_type, zone2.region_type):
                    continue

                # fleet sticks to special coats, army to the container
                if not acceptable(unit_type, zone2):
                    continue

                # there must be an intersection in the polygon
                assert zone2.polygon is not None
                if not adjacent(zone1.polygon, zone2.polygon):
                    continue

                dict_unit_type[str(zone1.number)].append(zone2.number)
                print(f"    {zone2}({zone2.number}) is adjacent")

        result_queue.put(dict_unit_type)
        print(f"Done with {'army' if unit_type == 1 else 'fleet'}.")

    # create zone
    for num_zone_str, zone_data in json_parameters_data['zones'].items():
        if zone_data['full_name']:
            zone = Zone(int(num_zone_str), zone_data['full_name'])
        else:
            for num, (num_zone2, num_coast) in enumerate(json_variant_data['coastal_zones']):
                if num + 1 == int(num_zone_str) - len(json_variant_data['regions']):
                    zone2 = Zone.nomenclature[num_zone2]
                    coast_name = json_parameters_data['coasts'][str(num_coast)]['name']
                    break
            zone = Zone(int(num_zone_str), f"{str(zone2)} {coast_name}")

    # put type from variant
    for num, region_type in enumerate(json_variant_data['regions']):
        num_zone = num + 1
        zone = Zone.nomenclature[num_zone]
        zone.put_region_type(region_type)

    # put type for special zones
    for num, _ in enumerate(json_variant_data['coastal_zones']):
        num_zone = len(json_variant_data['regions']) + int(num) + 1
        zone = Zone.nomenclature[num_zone]
        zone.put_region_type(1)

    # put poly from parameters
    for num_zone_str, zone_area_data in json_parameters_data['zone_areas'].items():
        polygon = zone_area_data['area']
        num_zone = int(num_zone_str)
        zone = Zone.nomenclature[num_zone]
        polygon_enhanced = polygon.copy()
        polygon_enhanced.append(polygon_enhanced[0])
        zone.put_polygon(polygon_enhanced)

    # create queus to collect result
    army_result_queue: multiprocessing.Queue[typing.Dict[str, typing.List[int]]] = multiprocessing.Queue()
    fleet_result_queue: multiprocessing.Queue[typing.Dict[str, typing.List[int]]] = multiprocessing.Queue()

    # fork process for armies
    army_running_process = multiprocessing.Process(target=processed_evaluate, args=(1, army_result_queue))
    army_running_process.start()

    # fork process for fleet
    fleet_running_process = multiprocessing.Process(target=processed_evaluate, args=(2, fleet_result_queue))
    fleet_running_process.start()

    # join processes
    army_running_process.join()
    fleet_running_process.join()

    # collect data
    new_neighbouring = []

    dict_unit_type = army_result_queue.get()
    new_neighbouring.append(dict_unit_type)

    dict_unit_type = fleet_result_queue.get()
    new_neighbouring.append(dict_unit_type)

    # now we prune coasts for fleets : two neighbouring coasts must see the same sea

    # build 'seas_of_zones'
    seas_of_zones: typing.Dict[Zone, typing.Set[Zone]] = collections.defaultdict(set)
    for zone_num1, neighbours in new_neighbouring[1].items():
        zone1 = Zone.nomenclature[int(zone_num1)]
        if zone1.region_type != 1:  # coast
            continue
        for zone_num2 in neighbours:
            zone2 = Zone.nomenclature[int(zone_num2)]
            if zone2.region_type != 3:  # sea
                continue
            seas_of_zones[zone1].add(zone2)

    # prune
    for zone_num1, neighbours in new_neighbouring[1].items():
        zone1 = Zone.nomenclature[int(zone_num1)]
        if zone1.region_type != 1:  # coast
            continue
        for zone_num2 in neighbours:
            zone2 = Zone.nomenclature[int(zone_num2)]
            if zone2.region_type != 1:  # coast
                continue
            if not seas_of_zones[zone1] & seas_of_zones[zone2]:
                print(f"Removing {zone2}({zone2.number}) from neighbours of {zone1}({zone1.number}) because no common sea")
                neighbours.remove(zone_num2)

    old_neighbouring = json_variant_data['neighbouring'].copy()

    # now let's show changes
    for num, (old_dict_unit_type, new_dict_unit_type) in enumerate(zip(old_neighbouring, new_neighbouring)):
        for (old_zone_num, old_neighbours), (new_zone_num, new_neighbours) in zip(old_dict_unit_type.items(), new_dict_unit_type.items()):
            if new_zone_num != old_zone_num:
                print(f"ERROR : By {'army' if num == 0 else 'fleet'} Zone number {old_zone_num} became {new_zone_num}")
                continue
            gained_items = set(new_neighbours) - set(old_neighbours)
            if gained_items:
                zone = Zone.nomenclature[int(new_zone_num)]
                print(f"By {'army' if num == 0 else 'fleet'} {str(zone)} gained : {[str(Zone.nomenclature[n]) for n in gained_items]}")
            lost_items = set(old_neighbours) - set(new_neighbours)
            if lost_items:
                zone = Zone.nomenclature[int(new_zone_num)]
                print(f"By {'army' if num == 0 else 'fleet'} {str(zone)} lost : {[str(Zone.nomenclature[n]) for n in lost_items]}")

    # now put changes in json
    json_variant_data['neighbouring'] = new_neighbouring


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

    # save neighbouring in file to add to variant file
    output = json.dumps(json_variant_data, indent=4, ensure_ascii=False)
    with open(variant_file, 'w', encoding='utf-8') as write_file:
        write_file.write(output)


if __name__ == "__main__":
    main()
