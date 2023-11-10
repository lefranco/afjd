#!/usr/bin/env python3


"""
Calculates distancing, the boring part of variant file
"""

import argparse
import json
import sys
import typing
import os


# if reached, there is a problem !
MAX_DIST = 20


def main() -> None:
    """ main """

    def check_non_reflexivity(neighbouring: typing.Dict[int, typing.Set[int]]) -> None:
        """ checks no zone is neighbour to itself """

        for zone, neighbours in neighbouring.items():
            assert zone not in neighbours, f"Problem with {zone=} neighbouring itself"

    def check_types(neighbouring: typing.Dict[int, typing.Set[int]]) -> None:
        """ checks army neighboring considers land ans coasts and fleet neighboring considers sea and coasts """

        def check_type(zone: int) -> None:
            if neighbouring == neighbouring_army:
                assert zone2type[zone] in [1, 2], f"Problem with {zone=} as army"
            else:
                assert zone2type[zone] in [1, 3], f"Problem with {zone=} as fleet"

        for zone, neighbours in neighbouring.items():
            check_type(zone)
            for zone1 in neighbours:
                check_type(zone1)

    def check_symetry(neighbouring: typing.Dict[int, typing.Set[int]]) -> None:
        """ checks that is A sees B, B sees A """

        for unit, neighbours in neighbouring.items():
            for unit2 in neighbours:
                assert unit in neighbouring[unit2], f"By {'army' if neighbouring==neighbouring_army else 'fleet'} {unit2} neighbour of {unit} but not the other way round"

    def distance(role: int, zone: int) -> int:
        """ distance of role to zone is lesser distance of start units to zone """

        dist = 0

        reachables = {center2region[c] for c in start_centers[role]}

        while True:

            # have we reached it ?
            if zone2region[zone] in map(lambda z: zone2region[z], reachables):
                return dist

            # calculate more
            new_ones = set.union(*(neighbouring[z] for z in reachables))

            # put them in
            reachables.update(new_ones)

            dist += 1
            assert dist <= MAX_DIST, f"Infinite loop ! for {role=} {zone=}"

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--variant_file', required=True, help='Load variant json file')
    args = parser.parse_args()

    json_variant_file = args.variant_file

    if not os.path.exists(json_variant_file):
        print(f"File '{json_variant_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    # load variant from json data file
    with open(json_variant_file, "r", encoding='utf-8') as read_file:
        try:
            json_variant_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {json_variant_file} : {exception}")
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

    roles = list(range(1, roles_['number'] + 1))
    #  print(f"{roles=}")

    regions = list(range(1, len(regions_) + 1))
    #  print(f"{regions=}")

    zone2type = {i + 1: t for i, t in enumerate(regions_)}
    zone2type.update({len(regions) + 1 + i: 1 for i in range(len(coastal_zones))})
    #  print(f"{zone2type=}")

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

    check_non_reflexivity(neighbouring_army)
    check_symetry(neighbouring_army)
    check_types(neighbouring_army)

    neighbouring_fleet = {int(zone): set(neighbours) for zone, neighbours in neighbouring_[1].items()}
    #  print(f"{neighbouring_fleet=}")

    check_non_reflexivity(neighbouring_fleet)
    check_symetry(neighbouring_fleet)
    check_types(neighbouring_fleet)

    neighbouring = {z: (neighbouring_army[z] if z in neighbouring_army else set()) | (neighbouring_fleet[z] if z in neighbouring_fleet else set()) for z in list(neighbouring_army.keys()) + list(neighbouring_fleet.keys())}

    distancing = []
    for _ in range(2):
        distancing_type = []
        for role in roles:
            distancing_role_type = {}
            for zone in zones:
                distancing_role_type[str(zone)] = distance(role, zone)
            distancing_type.append(distancing_role_type)
        distancing.append(distancing_type)
    #  print(f"{distancing=}")

    json_variant_data['distancing'] = distancing

    # save distancing in file to add to variant file
    output = json.dumps(json_variant_data, indent=4, ensure_ascii=False)
    with open(json_variant_file, 'w', encoding='utf-8') as write_file:
        write_file.write(output)


if __name__ == '__main__':
    main()
