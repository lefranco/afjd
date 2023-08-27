#!/usr/bin/env python3


"""
File : check_json.py

parses to check json files
"""

import argparse
import json
import sys
import typing


def main() -> None:
    """ main """

    def check_symetry(neighbouring: typing.Dict[int, typing.Set[int]]) -> None:

        for unit, neighbours in neighbouring.items():
            for unit2 in neighbours:
                if unit not in neighbouring[unit2]:
                    print(f"WARNING : By {'army' if neighbouring==neighbouring_army else 'fleet'} {unit2} neighbour of {unit} but not the other way round")

    def distance(role: int, zone: int) -> int:

        dist = 0

        reachables = {center2region[c] for c in start_centers[role]}

        while True:

            if zone2region[zone] in map(lambda z: zone2region[z], reachables):
                return dist

            new_ones = set.union(*(neighbouring[z] for z in reachables))

            reachables.update(new_ones)

            dist += 1
            assert dist <= 30, f"Infinite loop ! for {role=} {zone=}"

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--variant_input', required=True, help='Input variant json file')
    parser.add_argument('-d', '--distancing_output', required=True, help='Output distacnce json file')
    args = parser.parse_args()

    json_variant_input = args.variant_input
    json_distancing_output = args.distancing_output

    # load variant from json data file
    with open(json_variant_input, "r", encoding='utf-8') as read_file:
        try:
            json_variant_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {json_variant_input} : {exception}")
            sys.exit(-1)

    regions_ = json_variant_data['regions']
    #  print(f"{regions=}")

    centers = json_variant_data['centers']
    #  print(f"{centers=}")

    roles_ = json_variant_data['roles']
    #  print(f"{roles_=}")

    start_centers_ = json_variant_data['start_centers']
    #  print(f"{start_centers_=}")

    coastal_zones = json_variant_data['coastal_zones']
    #  print(f"{coastal_zones=}")

    neighbouring_ = json_variant_data['neighbouring']
    #  print(f"{neighbouring_=}")

    # TODO : compare this old one with result
    #  distancing_ = json_variant_data['distancing']
    #  print(f"{distancing__=}")

    roles = list(range(1, roles_['number'] + 1))
    #  print(f"{roles=}")

    regions = list(range(1, len(regions_) + 1))
    #  print(f"{regions=}")

    start_centers = {i + 1: s for i, s in enumerate(start_centers_)}
    #  print(f"{start_centers=}")

    center2region = {i + 1: r for i, r in enumerate(centers)}
    #  print(f"{center2region=}")

    zone2region = {z: z for z in range(1, len(regions) + 1)}
    zone2region.update({len(regions) + 1 + i: r for (i, (r, _)) in enumerate(coastal_zones)})
    #  print(f"{zone2region=}")

    zones = list(zone2region.keys())
    #  print(f"{zones=}")

    neighbouring_army = {int(zone): set(neighbours) for zone, neighbours in neighbouring_[0].items()}
    #  print(f"{neighbouring_army=}")

    check_symetry(neighbouring_army)

    neighbouring_fleet = {int(zone): set(neighbours) for zone, neighbours in neighbouring_[1].items()}
    #  print(f"{neighbouring_fleet=}")

    check_symetry(neighbouring_fleet)

    neighbouring = {z: (neighbouring_army[z] if z in neighbouring_army else set()) | (neighbouring_fleet[z] if z in neighbouring_fleet else set()) for z in list(neighbouring_army.keys()) + list(neighbouring_fleet.keys())}

    distancing = []
    for role in roles:
        distancing_role = []
        for _ in range(2):
            distancing_type_role = {}
            for zone in zones:
                distancing_type_role[str(zone)] = distance(role, zone)
            distancing_role.append(distancing_type_role)
        distancing.append(distancing_role)
    #  print(f"{distancing=}")

    json_output_data = {'distancing': distancing}

    output = json.dumps(json_output_data, indent=4)
    with open(json_distancing_output, 'w', encoding='utf-8') as write_file:
        write_file.write(output)


if __name__ == '__main__':
    main()
