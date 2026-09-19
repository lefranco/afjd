#!/usr/bin/env python3


"""Check balance.

for windows only, add this line:
   sys.stdout.reconfigure(encoding='utf-8')
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys
import typing

NUMBER = 0

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

ARMY = 1
FLEET = 2


def compatible(type_unit: int, num_region: int) -> bool:
    """Say if this type of unit can go on this type of region."""
    # 1 = coast
    # 2 = earth
    # 3 = sea
    # 4 = island

    # determine type of zone
    type_zone = JSON_VARIANT_DATA['regions'][num_region - 1]
    assert type_zone in (1, 2, 3, 4)

    if type_unit == 1:  # army
        return type_zone in (1, 2, 4)

    # fleet
    return type_zone in (1, 3, 4)


def can_reach(type_unit: int, unit_zone: int, destination: int) -> bool:
    """Apply neighbouring to see if access is possible."""
    return str(unit_zone) in JSON_VARIANT_DATA['neighbouring'][type_unit - 1] and destination in JSON_VARIANT_DATA['neighbouring'][type_unit - 1][str(unit_zone)]


def check_starting_units() -> None:
    """check_starting_units."""
    global NUMBER
    NUMBER += 1
    print("============")
    print(f"{NUMBER}. Starting units stats.")
    print("Rationale: we expect factions to have an approximatively equal number of armies and fleets. \nThere should be at least one of each, and no more than one between them.")
    print("============")

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :")
        stats[role_num] = 0

        armies = fleets = 0
        for unit, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            if unit == '1':
                armies = len(zones)
            else:
                fleets = len(zones)
        stats[role_num] = armies + fleets
        print(f"\t\tstarts with {armies} armie(s) and {fleets} fleet(s)")
        if not armies:
            print("\t\thas no armies to start with ⚠️ ")
        if not fleets:
            print("\t\thas no fleets to start with ⚠️ ")
        if abs(fleets - armies) > 1:
            print("\t\thas more than one as difference between number of armies and fleets to start with  ⚠️ ")

    # print(f"{stats=}")
    print(f"Deviation is {statistics.stdev(stats.values()):0.3f}")
    print()


def check_all_direct_center_access() -> None:
    """check_all_direct_center_access."""
    global NUMBER
    NUMBER += 1
    print("============")
    print(f"{NUMBER}. Centers reachable on the first move.")
    print("Rationale: we expect factions to have approximatively the same opportunity to reach a center in the very first move.\nEither all af them can, or none of them can. We do not expect a faction to directly reach anothr faction's home center.")
    print("============")

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :", end='')
        stats[role_num] = 0

        has_one = False
        for num_center, num_region in enumerate(JSON_VARIANT_DATA['centers']):
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
                                print(f"\n\t\t{CENTER_NAME_TABLE[num_center + 1]}: ", end='')
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
    """check_contested_direct_center_access."""
    global NUMBER
    NUMBER += 1
    print("============")
    print(f"{NUMBER}. Centers reachable on the first move (contested or not by more than one faction).")
    print("Rationale: we expect factions to have approximatively the same possibilties of reaching centers at firt move, whether  contested by another faction or not. Either every factions has one garanteed center or none does.")
    print("============")

    access_table = collections.defaultdict(set)
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        for type_unit_str, zones in JSON_VARIANT_DATA['start_units'][role_num - 1].items():
            type_unit = int(type_unit_str)
            for zone_unit in zones:
                for num_zone_dest in range(1, len(JSON_VARIANT_DATA['regions']) + len(JSON_VARIANT_DATA['coastal_zones']) + 1):
                    if can_reach(type_unit, zone_unit, num_zone_dest) and num_zone_dest in CENTER_ZONE_TABLE:
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
    """check_distances_to_win."""
    global NUMBER
    NUMBER += 1
    print("============")
    print(f"{NUMBER}. Distance to reach a solo victory.")
    print("Rationale: we calculate how many moves it takes each factions to reach a solo victory.\nWe expect factions to have approximatively same value.")
    print("============")

    debug = False

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :")

        # initialize 'zones_reached'
        # any unit buildable a start position
        zones_reached: set[tuple[int, int]] = set()

        # first we determine all satrting zones
        start_zones = set()
        for type_unit in (1, 2):
            for zone in JSON_VARIANT_DATA['start_units'][role_num - 1][str(type_unit)]:
                start_zones.add(zone)

        # for all regions that include a strting zone
        zones_reached = set()
        for region, zones in REGION_ZONES_TABLE.items():
            if any(z in start_zones for z in zones):
                # iterate other all possible built units
                for zone_unit in zones:
                    for type_unit in (ARMY, FLEET):
                        # on special coast
                        if zone_unit > len(JSON_VARIANT_DATA['regions']):
                            if type_unit == FLEET:
                                zones_reached.add((type_unit, zone_unit))
                        # not on special coast
                        elif compatible(type_unit, region):
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

            # zones -> centers
            centers_reached = set()
            for num_center, num_region in enumerate(JSON_VARIANT_DATA['centers']):
                if any(z in REGION_ZONES_TABLE[num_region] for z in (zr[1] for zr in zones_reached)):
                    centers_reached.add(num_center + 1)
            if debug:
                print(f"\t\t\tAfter {steps=} {len(centers_reached)} centers: {' '.join(CENTER_NAME_TABLE[c] for c in centers_reached)}")
            nb_centers = len(centers_reached)

            # are we done ?
            if nb_centers == solo_value:
                value = float(steps)
                break

            if nb_centers > solo_value:
                frac = (solo_value - prev_nb_centers) / (nb_centers - prev_nb_centers)
                if debug:
                    print(f"\t\t\t{nb_centers=} {prev_nb_centers=} {solo_value=} {frac=}")
                assert (0 < frac < 1), f"Error in {frac=}"
                value = steps - 1 + frac
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
    """check_safe_home_center."""
    global NUMBER
    NUMBER += 1
    print("============")
    print(f"{NUMBER}. Safe home centers.")
    print("Rationale: we expect that no faction can reach home center of other faction by the first autumn.\nIf this is possible can, than we expect it to be balanced, with no faction to be immune.")
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
        start_centers = set(JSON_VARIANT_DATA['start_centers'][role_num - 1])
        safe_centers = start_centers

        for role_num2 in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
            if str(role_num2) in JSON_VARIANT_DATA['disorder']:
                continue

            if role_num2 == role_num:
                continue

            if occupied_zone_centers := faction_reached[role_num2] & faction_zone_centers[role_num]:
                occupied_centers = [CENTER_ZONE_TABLE[z] for z in occupied_zone_centers]
                stats[role_num] += len(occupied_centers)
                centers_names = ' '.join([CENTER_NAME_TABLE[c] for c in occupied_centers])
                print(f"\t\tHome center(s) {centers_names} can be occupied by a unit of {ROLE_NAME_TABLE[role_num2]}")
                safe_centers -= set(occupied_centers)

        if not safe_centers:
            print("\t\tHas no safe centers ⚠️")
        else:
            centers_names = ' '.join([CENTER_NAME_TABLE[c] for c in safe_centers])
            print(f"\t\tSafe centers : {centers_names}")

        print(f"\t\t -- Its home centers can be occupied {stats[role_num]} time(s). --")

    # print(f"{stats=}")
    print(f"Deviation is {statistics.stdev(stats.values()):0.3f}")
    print()


def check_easy_center() -> None:
    """check_easy_center."""
    global NUMBER
    NUMBER += 1
    print("============")
    print(f"{NUMBER}. Easy centers.")
    print("Rationale: we expect that no faction can reach a center by the first autumn with no possible oppostion. If such possibility exists, then we expect this to be balanced, with each factions having the same opportunities.")
    print("============")

    debug = True

    faction_centers = {}

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

        # zones centers
        centers = {CENTER_ZONE_TABLE[z] for _, z in zones_reached if z in CENTER_ZONE_TABLE}

        # remove starting centers
        centers -= set(JSON_VARIANT_DATA['start_centers'][role_num - 1])

        # keep a note of centers reached
        faction_centers[role_num] = centers

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :")

        if debug:
            print("\t\tReachable: ")
            print(f"\t\t\t{' '.join([CENTER_NAME_TABLE[c] for c in faction_centers[role_num]])}")

        other_active_roles = set(range(1, JSON_VARIANT_DATA['roles']['number'] + 1)) - {role_num} - set(map(int, JSON_VARIANT_DATA['disorder'].keys()))

        # centers I can reach
        easy_centers = faction_centers[role_num].copy()

        # centers other can reached removed
        easy_centers -= set().union(*[faction_centers[r] for r in other_active_roles])

        # other home centers removed
        easy_centers -= set().union(*[JSON_VARIANT_DATA['start_centers'][r - 1] for r in other_active_roles])

        print("\t\tEasy centers: ")
        print(f"\t\t\t{' '.join([CENTER_NAME_TABLE[c] for c in easy_centers])}")

        stats[role_num] = len(easy_centers)

    # print(f"{stats=}")
    print(f"Deviation is {statistics.stdev(stats.values()):0.3f}")
    print()


def check_no_initial_threats() -> None:
    """check_no_initial_threats."""
    global NUMBER
    NUMBER += 1
    print("============")
    print(f"{NUMBER}. Inital threats.")
    print("Rationale: we expect no factions to be able to make an opening move that threatens more than one of another faction's starting centers (aside from a neutral center). If such move exists, then we expect this to be balanced, with each factions having the same number of active and passive threats of this kind.")
    print("============")

    print("  Threats:")
    print()

    number_threats = 2
    threatens: collections.Counter[int] = collections.Counter()
    threatened: collections.Counter[int] = collections.Counter()
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue

        print(f"\t{ROLE_NAME_TABLE[role_num]} :")

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

                        print(f"\t\tMoving {TYPE_UNIT_NAME_TABLE[type_unit][0]} {ZONE_NAME_TABLE[zone_unit]} to {ZONE_NAME_TABLE[num_new_zone]} creates {len(threatening)} threat(s):", end='')
                        print(f" {' '.join([CENTER_NAME_TABLE[c] for c in threatening])}", end='')

                        neutrals = [c for c in threatening if c not in OWNER_TABLE]
                        owned = collections.defaultdict(list)
                        for center in threatening:
                            if center in OWNER_TABLE:
                                owned[OWNER_TABLE[center]].append(center)
                        if not (neutrals and any(len(v) >= number_threats for v in owned.values())):
                            print()
                            continue

                        print(" ⚠️  ", end='')
                        threatens[role_num] += 1
                        for k, v in owned.items():
                            if len(v) < number_threats:
                                continue
                            threatened[k] += 1
                            print(f"/{ROLE_NAME_TABLE[k]}: {' '.join([CENTER_NAME_TABLE[c] for c in v])} ", end='')
                        print()

    print()
    print("  Recap:")
    print()
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue
        print(f"\t{ROLE_NAME_TABLE[role_num]} :")
        print(f"\t\tThreatens {threatens[role_num]} times and is threatened {threatened[role_num]} times")
        if abs(threatens[role_num] - threatened[role_num]) > 1:
            print("\t\tWe have a too big difference here ⚠️  ")

    delta = {r: threatens[r] - threatened[r] for r in range(1, JSON_VARIANT_DATA['roles']['number'] + 1)}

    print()
    print(f"Deviation for active is {statistics.stdev(threatens.values()):0.3f}")
    print(f"Deviation for passive is {statistics.stdev(threatened.values()):0.3f}")
    print(f"Deviation for delta is {statistics.stdev(delta.values()):0.3f}")
    print()


def check_unit_defensive_effectiveness() -> None:
    """check_unit_defensive_effectiveness."""

    def compute(unit_type: int, role_num: int) -> float:
        """Compute."""
        regions = set()
        for num_region in range(1, len(JSON_VARIANT_DATA['regions']) + 1):

            if not compatible(unit_type, num_region):
                continue

            for zone in REGION_ZONES_TABLE[num_region]:
                if zone in CENTER_ZONE_TABLE and CENTER_ZONE_TABLE[zone] in OWNER_TABLE and OWNER_TABLE[CENTER_ZONE_TABLE[zone]] == role_num:
                    regions.add(num_region)
                    if debug:
                        print(f"\t\tadd {ZONE_NAME_TABLE[zone]} as center")
                    for num_region2 in range(1, len(JSON_VARIANT_DATA['regions']) + 1):
                        for zone2 in REGION_ZONES_TABLE[num_region2]:
                            if can_reach(unit_type, zone, zone2):
                                regions.add(num_region2)
                                if debug:
                                    print(f"\t\t\t + {ZONE_NAME_TABLE[zone2]} as next to home center")

        if debug:
            print("\t\tNeed to consider: ", end='')
            print(f"{' '.join([ZONE_NAME_TABLE[z] for z in regions])}")

        unit_defensive_effectiveness_table: dict[int, int] = collections.defaultdict(int)
        for num_region in regions:

            for zone in REGION_ZONES_TABLE[num_region]:
                if zone in CENTER_ZONE_TABLE and CENTER_ZONE_TABLE[zone] in OWNER_TABLE and OWNER_TABLE[CENTER_ZONE_TABLE[zone]] == role_num:
                    unit_defensive_effectiveness_table[num_region] += 1
                    break

            for zone1 in REGION_ZONES_TABLE[num_region]:
                for num_region2 in range(1, len(JSON_VARIANT_DATA['regions']) + 1):
                    for zone2 in REGION_ZONES_TABLE[num_region2]:
                        if zone2 in CENTER_ZONE_TABLE and CENTER_ZONE_TABLE[zone2] in OWNER_TABLE and OWNER_TABLE[CENTER_ZONE_TABLE[zone2]] == role_num and can_reach(unit_type, zone1, zone2):
                            unit_defensive_effectiveness_table[num_region] += 1
                            break

        if debug:
            print("\t\tAfter step 1:")
            for k, v in unit_defensive_effectiveness_table.items():
                print(f"\t\t\t{ZONE_NAME_TABLE[k]}: {v}")

        for num_region in unit_defensive_effectiveness_table:
            unit_defensive_effectiveness_table[num_region] -= 1

        if debug:
            print("\t\tAfter step 2:")
            for k, v in unit_defensive_effectiveness_table.items():
                print(f"\t\t\t{ZONE_NAME_TABLE[k]}: {v}")

        for num_region in unit_defensive_effectiveness_table:
            if num_region in CENTER_ZONE_TABLE:
                unit_defensive_effectiveness_table[num_region] += 1

        if debug:
            print("\t\tAfter step 3:")
            for k, v in unit_defensive_effectiveness_table.items():
                print(f"\t\t\t{ZONE_NAME_TABLE[k]}: {v}")

        unit_defensive_effectiveness = float(sum(unit_defensive_effectiveness_table.values()))
        unit_defensive_effectiveness *= 3.
        unit_defensive_effectiveness /= len(JSON_VARIANT_DATA['start_centers'][role_num - 1])

        if debug:
            print("\t\tFinally:")
            print(f"\t\t\t{unit_defensive_effectiveness=}")

        return unit_defensive_effectiveness

    global NUMBER
    NUMBER += 1
    print("============")
    print(f"{NUMBER}. Unit defensive effectiveness.:")
    print("Rationale: we compute 'Unit defensive effectiveness' for fleets and armies for all factions. \nWe expect the result to be higher for armies than fleets and the ratio armies/fleets balanced between factions...")
    print("============")

    debug = False

    stats = {}
    for role_num in range(1, JSON_VARIANT_DATA['roles']['number'] + 1):
        if str(role_num) in JSON_VARIANT_DATA['disorder']:
            continue
        print(f"\t{ROLE_NAME_TABLE[role_num]} :")

        print("\t\tArmies: ", end='')
        army_defensive_effectiveness = compute(1, role_num)
        print(f"{army_defensive_effectiveness}")

        print("\t\tFleets: ", end='')
        fleet_defensive_effectiveness = compute(2, role_num)
        print(f"{fleet_defensive_effectiveness}")

        if not army_defensive_effectiveness > fleet_defensive_effectiveness:
            print("\t\tArmies are not more effective than fleets ⚠️  ")

        stats[role_num] = army_defensive_effectiveness / fleet_defensive_effectiveness

    # print(f"{stats=}")
    print(f"Deviation is {statistics.stdev(stats.values()):0.3f}")
    print()


def main() -> None:
    """Do main."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    parser.add_argument('-v', '--variant_file', required=True, help='variant file')
    args = parser.parse_args()

    #  load files at start
    parameters_path = pathlib.Path(args.parameters_file)
    variant_path = pathlib.Path(args.variant_file)

    # load parameters from json data file
    if not parameters_path.exists():
        print(f"File '{parameters_path}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    with pathlib.Path.open(parameters_path, encoding='utf-8') as read_file:
        try:
            global JSON_PARAMETERS_DATA
            JSON_PARAMETERS_DATA = json.load(read_file)
        except json.JSONDecodeError as exception:
            print(f"Failed to load {parameters_path} : {exception}")
            sys.exit(-1)

    # load variant from json data file
    if not variant_path.exists():
        print(f"File '{variant_path}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    # load parameters from json data file
    with pathlib.Path.open(variant_path, encoding='utf-8') as read_file:
        try:
            global JSON_VARIANT_DATA
            JSON_VARIANT_DATA = json.load(read_file)
        except json.JSONDecodeError as exception:
            print(f"Failed to load {variant_path} : {exception}")
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

    check_starting_units()
    check_all_direct_center_access()
    check_contested_direct_center_access()
    check_distances_to_win()
    check_safe_home_center()
    check_easy_center()
    check_no_initial_threats()
    check_unit_defensive_effectiveness()


if __name__ == '__main__':
    main()
