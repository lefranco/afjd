#!/usr/bin/env python3


"""
Check balance
"""

import os
import json
import argparse
import sys
import typing
import collections
import statistics


JSON_PARAMETERS_DATA: dict[str, typing.Any] = {}
JSON_VARIANT_DATA: dict[str, typing.Any] = {}

ROLE_NAME_TABLE: dict[int, str] = {}
TYPE_UNIT_NAME_TABLE: dict[int, str] = {}
ZONE_NAME_TABLE: dict[int, str] = {}
COAST_NAME_TABLE: dict[int, str] = {}
CENTER_NAME_TABLE: dict[int, str] = {}

REGION_ZONES_TABLE: dict[int, list[int]] = {}
CENTER_ZONE_TABLE: dict[int, int] = {}
OWNER_TABLE: dict[int, int] = {}


def can_reach(type_unit: int, unit_zone: int, destination: int) -> bool:
    """ Apply neighbouring to see if access is possible"""
    return str(unit_zone) in JSON_VARIANT_DATA['neighbouring'][type_unit - 1] and destination in JSON_VARIANT_DATA['neighbouring'][type_unit - 1][str(unit_zone)]


def check_all_direct_center_access() -> None:
    """check_all_direct_center_access"""

    print("============")
    print("1. Factions that can reach a center in first moves:")
    print("============")

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :", end='')
        stats[role_num] = 0

        has_one = False
        for num_center, num_region in sorted(enumerate(JSON_VARIANT_DATA['centers']), key=lambda t: CENTER_NAME_TABLE[t[0] + 1]):
            center_printed = False
            for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
                type_unit = int(type_unit_str)
                for zone_unit in zones:
                    if num_center + 1 in JSON_VARIANT_DATA['start_centers'][role_num - 1]:
                        continue
                    for num_zone in REGION_ZONES_TABLE[num_region]:
                        if can_reach(type_unit, zone_unit, num_zone):
                            stats[role_num] += 1
                            if not center_printed:
                                print(f"\n\t\t{CENTER_NAME_TABLE[num_center]}: ", end='')
                                center_printed = True
                            else:
                                print("/ ", end='')
                            print(f"from {TYPE_UNIT_NAME_TABLE[type_unit][0]} in {ZONE_NAME_TABLE[zone_unit]} ", end='')
                            if num_center + 1 in OWNER_TABLE and OWNER_TABLE[num_center + 1] != role_num:
                                print(f" (start center of {ROLE_NAME_TABLE[OWNER_TABLE[num_center + 1]]} ⚠️ )", end='')
                            has_one = True
        if not has_one:
            print("\n\t\tHas no direct access to any center ⚠️ ")

        print()

    # print(f"{stats=}")
    print(f"Deviation is {statistics.stdev(stats.values()):0.3f}")
    print()


def check_contested_direct_center_access() -> None:
    """check_contested_direct_center_access"""

    print("============")
    print("2. Centers that can be reached in first move (contested or not by more than a faction):")
    print("============")

    access_table = collections.defaultdict(set)
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            type_unit = int(type_unit_str)
            for zone_unit in zones:
                for num_zone_dest in range(1, len(JSON_VARIANT_DATA['regions']) + len(JSON_VARIANT_DATA['coastal_zones']) + 1):
                    if can_reach(type_unit, zone_unit, num_zone_dest):
                        if num_zone_dest in CENTER_ZONE_TABLE:
                            center = CENTER_ZONE_TABLE[num_zone_dest]
                            if center in JSON_VARIANT_DATA['start_centers'][role_num - 1]:
                                continue
                            access_table[center].add(role_num)

    for num_center, factions in sorted(access_table.items(), key=lambda t: (len(t[1]), CENTER_NAME_TABLE[t[0]])):
        faction_names = ' '.join(ROLE_NAME_TABLE[f] for f in factions)
        if len(factions) > 1:
            print(f"\t{CENTER_NAME_TABLE[num_center]}:")
            print(f"\t\tcontested between {faction_names}")
        else:
            print(f"\t{CENTER_NAME_TABLE[num_center]}:")
            print(f"\t\twithout contest by {faction_names} alone ⚠️")

    print("(No deviation involved)")
    print()


def check_distances_to_win() -> None:
    """check_distances_to_win"""

    debug = False

    print("============")
    print("3. For every factions, the distance to reach the solo is:")
    print("============")

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :")

        # initialize 'zones_reached'
        # original units only (unlike superstition)
        zones_reached = set()
        for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            type_unit = int(type_unit_str)
            for zone_unit in zones:
                zones_reached.add((type_unit, zone_unit))

        # keep increasing 'zones_reached'
        steps = 1
        prev_nb_centers = 0
        solo_value = len(JSON_VARIANT_DATA['centers']) // 2 + 1
        while True:

            # increase zones
            for type_unit, zone_unit in zones_reached.copy():
                for num_new_zone in range(1, len(JSON_PARAMETERS_DATA['zones']) + 1):
                    if can_reach(type_unit, zone_unit, num_new_zone):
                        zones_reached.add((type_unit, num_new_zone))
            if debug:
                print(f"\t\t\tAfter {steps=} {len(zones_reached)} zones: {' '.join(ZONE_NAME_TABLE[zr[1]] for zr in zones_reached)}")

            # zones -> centers
            centers_reached = set()
            for num_center, num_region in enumerate(JSON_VARIANT_DATA['centers']):
                if any(z in REGION_ZONES_TABLE[num_region] for z in (zr[1] for zr in zones_reached)):
                    centers_reached.add(num_center + 1)
            if debug:
                print(f"\t\t\tAfter {steps=} {len(centers_reached)} centers: {' '.join(CENTER_NAME_TABLE[c] for c in centers_reached)}")
            if debug:
                print()
            nb_centers = len(centers_reached)

            # are we done ?
            if nb_centers == solo_value:
                value = float(steps)
                break

            if nb_centers > solo_value:
                frac = (nb_centers - solo_value) / (nb_centers - prev_nb_centers)
                if debug:
                    print(f"\t\t\t{nb_centers=} {prev_nb_centers=} {solo_value=} {frac=}")
                assert (0 < frac < 1), f"Error in {frac=}"
                value = steps + frac
                break

            # keep going
            prev_nb_centers = nb_centers
            steps += 1

        stats[role_num] = value
        print(f"\t\tvalue is {value:0.2f}")

    # print(f"{stats=}")
    print(f"Deviation is {statistics.stdev(stats.values()):0.3f}")
    print()


def check_safe_home_center() -> None:
    """check_safe_home_center"""

    print("============")
    print("4. Factions that some other faction can reach home center at first autumn:")
    print("============")

    faction_reached = {}
    faction_zone_centers = {}

    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        # initialize 'zones_reached'
        zones_reached = set()
        for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            type_unit = int(type_unit_str)
            for zone_unit in zones:
                zones_reached.add((type_unit, zone_unit))

        # make two moves
        for _ in range(2):

            # increase zones
            for type_unit, zone_unit in zones_reached.copy():
                for num_new_zone in range(1, len(JSON_PARAMETERS_DATA['zones']) + 1):
                    if can_reach(type_unit, zone_unit, num_new_zone):
                        zones_reached.add((type_unit, num_new_zone))

        # keep a note of what is reached
        faction_reached[role_num] = {tr[1] for tr in zones_reached}

        # zones of my centers
        zone_centers = set()
        for num_center, num_region in enumerate(JSON_VARIANT_DATA['centers']):
            if num_center + 1 not in JSON_VARIANT_DATA['start_centers'][role_num - 1]:
                continue
            zone_centers |= set(REGION_ZONES_TABLE[num_region])

        # keep a note of zone occupying my centers
        faction_zone_centers[role_num] = zone_centers

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :")
        stats[role_num] = 0

        for role_num2 in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
            if str(role_num2) in JSON_VARIANT_DATA['disorder']:
                continue

            if role_num2 == role_num:
                continue

            if occupied := faction_reached[role_num2] & faction_zone_centers[role_num]:
                stats[role_num] += len(occupied)
                centers_names = ' '.join([CENTER_NAME_TABLE[CENTER_ZONE_TABLE[z]] for z in occupied])
                print(f"\t\tHome center {centers_names} can be occupied by a unit of {ROLE_NAME_TABLE[role_num2]}")

    # print(f"{stats=}")
    print(f"Deviation is {statistics.stdev(stats.values()):0.3f}")
    print()


def check_no_initial_threats() -> None:
    """check_no_initial_threats"""

    print("============")
    print("5. No unit can start with a move that both threatens more than one of another faction's starting centers besides a neutral center:")
    print("============")

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :")
        stats[role_num] = 0

        # for every starting unit
        for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            type_unit = int(type_unit_str)
            for zone_unit in zones:

                # where can it go
                for num_new_zone in range(1, len(JSON_PARAMETERS_DATA['zones']) + 1):
                    if can_reach(type_unit, zone_unit, num_new_zone):

                        # what does it threatens
                        threatening = set()
                        for num_new_new_zone in range(1, len(JSON_PARAMETERS_DATA['zones']) + 1):

                            if num_new_new_zone == zone_unit:
                                continue
                            if num_new_new_zone not in CENTER_ZONE_TABLE:
                                continue
                            if CENTER_ZONE_TABLE[num_new_new_zone] in OWNER_TABLE and OWNER_TABLE[CENTER_ZONE_TABLE[num_new_new_zone]] == role_num:
                                continue
                            if can_reach(type_unit, num_new_zone, num_new_new_zone):
                                threatening.add(CENTER_ZONE_TABLE[num_new_new_zone])

                        if not threatening:
                            continue

                        print(f"\t\tMoving {TYPE_UNIT_NAME_TABLE[type_unit][0]} {ZONE_NAME_TABLE[zone_unit]} to {ZONE_NAME_TABLE[num_new_zone]} makes {len(threatening)} threats:", end='')
                        print(f" {' '.join([CENTER_NAME_TABLE[c] for c in threatening])}", end='')

                        neutrals = [c for c in threatening if c not in OWNER_TABLE]
                        if len(threatening) - len(neutrals) < 2:
                            print()
                            continue

                        owned = collections.defaultdict(list)
                        for center in threatening:
                            if center in OWNER_TABLE:
                                owned[OWNER_TABLE[center]].append(center)
                        if not any(len(v) >= 2 for v in owned.values()):
                            print()
                            continue

                        print(" ⚠️  ", end='')
                        for k, v in owned.items():
                            print(f"/{ROLE_NAME_TABLE[k]}: {' '.join([CENTER_NAME_TABLE[c] for c in v])} ", end='')
                        print()


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    parser.add_argument('-v', '--variant_file', required=True, help='variant file')
    args = parser.parse_args()

    #  load files at start
    parameters_file = args.parameters_file
    variant_file = args.variant_file

    # load parameters from json data file
    if not os.path.exists(parameters_file):
        print(f"File '{parameters_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    with open(parameters_file, "r", encoding='utf-8') as read_file:
        try:
            global JSON_PARAMETERS_DATA
            JSON_PARAMETERS_DATA = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {parameters_file} : {exception}")
            sys.exit(-1)

    # load variant from json data file
    if not os.path.exists(variant_file):
        print(f"File '{variant_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    # load parameters from json data file
    with open(variant_file, "r", encoding='utf-8') as read_file:
        try:
            global JSON_VARIANT_DATA
            JSON_VARIANT_DATA = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {parameters_file} : {exception}")
            sys.exit(-1)

    # calculate some useful stuff

    # for printing
    global ROLE_NAME_TABLE
    ROLE_NAME_TABLE = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['roles'].items() if n != "0"}

    global TYPE_UNIT_NAME_TABLE
    TYPE_UNIT_NAME_TABLE = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['units'].items()}

    global ZONE_NAME_TABLE
    ZONE_NAME_TABLE = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['zones'].items() if d['name']}

    global COAST_NAME_TABLE
    COAST_NAME_TABLE = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['coasts'].items()}

    global CENTER_NAME_TABLE
    CENTER_NAME_TABLE = {n + 1: ZONE_NAME_TABLE[v] for n, v in enumerate(JSON_VARIANT_DATA['centers'])}

    # for locating special coasts
    global REGION_ZONES_TABLE
    REGION_ZONES_TABLE = {n: [n] for n in ZONE_NAME_TABLE}
    for zone_num, special in enumerate(JSON_VARIANT_DATA['coastal_zones'], start=len(ZONE_NAME_TABLE) + 1):
        ZONE_NAME_TABLE[zone_num] = f"{ZONE_NAME_TABLE[special[0]]}{COAST_NAME_TABLE[special[1]]}"
        REGION_ZONES_TABLE[special[0]].append(zone_num)

    # zone to center table
    for region, zones in REGION_ZONES_TABLE.items():
        if region in JSON_VARIANT_DATA['centers']:
            for zone in zones:
                CENTER_ZONE_TABLE[zone] = JSON_VARIANT_DATA['centers'].index(region) + 1

    # start centers
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        for num_center in JSON_VARIANT_DATA['start_centers'][role_num - 1]:
            OWNER_TABLE[num_center] = role_num

    # now do the checks

    check_all_direct_center_access()
    check_contested_direct_center_access()
    check_distances_to_win()
    check_safe_home_center()
    check_no_initial_threats()


if __name__ == '__main__':
    main()
