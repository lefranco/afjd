#!/usr/bin/env python3


"""
Check balance
"""

import os
import json
import argparse
import sys
import collections

JSON_PARAMETERS_DATA = None
JSON_VARIANT_DATA = None

def can_reach(type_unit, unit_zone, destination):    
    return str(unit_zone) in JSON_VARIANT_DATA['neighbouring'][type_unit - 1] and destination in JSON_VARIANT_DATA['neighbouring'][type_unit - 1][str(unit_zone)]


def check_all_direct_center_access():

    print("")
    print("Factions that can reach a center in first moves (contested or not):")
    print("")

    # for printing
    role_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['roles'].items() if n != "0"}
    type_unit_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['units'].items()}
    zone_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['zones'].items() if d['name']}
    coast_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['coasts'].items()}

    # for locating special coasts
    region_zones_table = {n : [n] for n in zone_name_table}
    for zone_num, special in enumerate(JSON_VARIANT_DATA['coastal_zones'], start=len(zone_name_table)+1):
        zone_name_table[zone_num] = f"{zone_name_table[special[0]]}{coast_name_table[special[1]]}"
        region_zones_table[special[0]].append(zone_num)

    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue
        print(f"\t{role_name_table[role_num]} :")
        has_one =  False
        for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            type_unit = int(type_unit_str)
            for zone_unit in zones:
                for num_center, num_region in enumerate(JSON_VARIANT_DATA['centers']):
                    if num_center + 1 in JSON_VARIANT_DATA['start_centers'][role_num - 1]:
                        continue
                    for num_zone in region_zones_table[num_region]:
                        if can_reach(type_unit, zone_unit, num_zone):
                            print(f"\t\t{type_unit_name_table[type_unit][0]} in {zone_name_table[zone_unit]} has direct access to center {zone_name_table[num_region]}", end='')
                            for other_role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
                                if other_role_num == role_num:
                                    continue
                                if num_center + 1 in JSON_VARIANT_DATA['start_centers'][other_role_num - 1]:
                                    print(f" (start center of {role_name_table[other_role_num]})", end='')
                                    break
                            print("")
                            has_one = True
        if not has_one:
            print("\t\tHas no direct access to any center ⚠️ ")


def check_uncontested_direct_center_access():

    print("")
    print("Factions that can reach a center in first moves (not contested):")
    print("")

    # for printing
    role_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['roles'].items() if n != "0"}
    zone_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['zones'].items() if d['name']}
    coast_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['coasts'].items()}

    # for locating special coasts
    region_zones_table = {n : [n] for n in zone_name_table}
    for zone_num, special in enumerate(JSON_VARIANT_DATA['coastal_zones'], start=len(zone_name_table)+1):
        zone_name_table[zone_num] = f"{zone_name_table[special[0]]}{coast_name_table[special[1]]}"
        region_zones_table[special[0]].append(zone_num)

    access_table = collections.defaultdict(set)
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue
        for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            type_unit = int(type_unit_str)
            for zone_unit in zones:
                for num_center, num_region in enumerate(JSON_VARIANT_DATA['centers']):
                    if num_center + 1 in JSON_VARIANT_DATA['start_centers'][role_num - 1]:
                        continue
                    for num_zone in region_zones_table[num_region]:
                        if can_reach(type_unit, zone_unit, num_zone):
                            access_table[num_center].add(role_num)

    for num_center, factions in access_table.items():
        faction_names = ' '.join(role_name_table[f] for f in factions)
        num_zone = JSON_VARIANT_DATA['centers'][num_center]
        if len(factions) > 1:
            print(f"\tCenter {zone_name_table[num_zone]} directly contested between {faction_names}")
        else:
            print(f"\tCenter {zone_name_table[num_zone]} directly taken without contest by {faction_names[0]} alone⚠️")


def check_distances_to_win():

    debug = False

    print("")
    print("For every factions, the distance to reach the solo is:")
    print("")

    # for printing
    role_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['roles'].items() if n != "0"}
    zone_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['zones'].items() if d['name']}
    coast_name_table = {int(n): d['name'] for n, d in JSON_PARAMETERS_DATA['coasts'].items()}
    center_name_table = {n+1 : zone_name_table[v] for n, v in enumerate(JSON_VARIANT_DATA['centers'])}

    # for locating special coasts
    region_zones_table = {n : [n] for n in zone_name_table}
    for zone_num, special in enumerate(JSON_VARIANT_DATA['coastal_zones'], start=len(zone_name_table)+1):
        zone_name_table[zone_num] = f"{zone_name_table[special[0]]}{coast_name_table[special[1]]}"
        region_zones_table[special[0]].append(zone_num)

    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue
        print(f"\t{role_name_table[role_num]} :")

        # initialize 'zones_reached'
        # original units only (unlike superstition)
        zones_reached = set()
        for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            type_unit = int(type_unit_str)            
            for zone_unit in zones:
                zones_reached.add((type_unit, zone_unit))

        # keep increasing 'zones_reached'
        nb_steps = 1
        prev_nb_centers = 0
        solo_value = len(JSON_VARIANT_DATA['centers']) // 2 + 1
        while True:

            # increase zones
            for type_unit, zone_unit in zones_reached.copy():
                for num_new_zone in range(1, len(JSON_PARAMETERS_DATA['zones']) + 1):
                    if can_reach(type_unit, zone_unit, num_new_zone):
                        zones_reached.add((type_unit, num_new_zone))
            if(debug): print(f"\t\t\tAfter {nb_steps=} {len(zones_reached)} zones: {' '.join(zone_name_table[zr[1]] for zr in zones_reached)}")

            # zones -> centers
            centers_reached = set()
            for num_center, num_region in enumerate(JSON_VARIANT_DATA['centers']):
                if any(z in region_zones_table[num_region] for z in (zr[1] for zr in zones_reached)):
                    centers_reached.add(num_center + 1)
            if(debug): print(f"\t\t\tAfter {nb_steps=} {len(centers_reached)} centers: {' '.join(center_name_table[c] for c in centers_reached)}")
            if(debug): print()
            nb_centers = len(centers_reached)

            # are we done ?
            if nb_centers == solo_value:
                break

            if nb_centers > solo_value:
                frac = (nb_centers - solo_value) / (nb_centers - prev_nb_centers)
                if(debug): print(f"\t\t\t{nb_centers=} {prev_nb_centers=} {solo_value=} {frac=}")
                assert (0 < frac < 1), f"Error in {frac=}"
                nb_steps += frac
                break

            # keep going
            prev_nb_centers = nb_centers
            nb_steps += 1

        print(f"\t\t{nb_steps=:0.2f}")
        #break # TODO remove




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

    check_all_direct_center_access()
    check_uncontested_direct_center_access()
    check_distances_to_win()



if __name__ == '__main__':
    main()
